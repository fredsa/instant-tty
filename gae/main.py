import cgi
import json
import webapp2

from . import compute
from . import error
from . import middleware
from . import model
from . import settings
from . import shared
from . import wsgi_config


_JSON_ENCODER = json.JSONEncoder()
_JSON_ENCODER.indent = 4
_JSON_ENCODER.sort_keys = True

_JSON_DECODER = json.JSONDecoder()

# From https://cloud.google.com/console/project/apps~little-black-box/apiui/credential
CLIENT_ID = '638064416490.apps.googleusercontent.com'

# TODO: create redirect URI dynamically
if shared.IsDevMode():
  redirect_uri = 'http://localhost:8080/'
else:
  redirect_uri = 'https://{}/'.format(app_identity.get_default_version_hostname())


def tojson(r):
  """Converts a Python object to JSON."""
  return _JSON_ENCODER.encode(r)


def fromjson(json):
  """Converts a JSON object into a Python object."""
  if json == '':
    return None
  return _JSON_DECODER.decode(json)


class AppHandler(webapp2.RequestHandler):
  """Convenience request handler with app specific functionality."""

  @webapp2.cached_property
  def user(self):
    return self.request.environ['app.user']

  def handle_exception(self, exception, debug_mode):
    """Called if this handler throws an exception during execution.

    Args:
      exception: the exception that was thrown
      debug_mode: True if the web application is running in debug mode
    """
    status, headers, body = error.MakeErrorResponse(exception, debug_mode)
    self.response.clear()
    self.error(status)
    self.response.headers.extend(headers)
    if self.response.headers.get('X-App-Error'):
      self.response.write(body)
    else:
      self.response.write('{}'.format(cgi.escape(body, quote=True)))

  def MakeOauth2Url(self):
    callbackuri = ('{}://{}/oauth2callback'
                   .format(self.request.scheme, self.request.host))
    scopes = '{}+{}'.format(settings.COMPUTE_SCOPE,
                            settings.STORAGE_SCOPE_READ_ONLY)
    # See https://developers.google.com/accounts/docs/OAuth2UserAgent
    return ('https://accounts.google.com/o/oauth2/auth'
            '?response_type=token'
            '&client_id={}'
            '&redirect_uri={}'
            '&scope={}'
            # '&state=foo'
            # '&approval_prompt=force'
            # '&login_hint={}'
            '&include_granted_scopes=false'
            .format(CLIENT_ID, callbackuri, scopes))

  def PerformAccessCheck(self):
    """Perform authorization checks.

    Subclasses must provide a suitable implementation.

    Raises:
      error.AppError if autorization check fails
    """
    raise NotImplementedError()

  def get(self):
    r = self.jsonget()
    self.response.headers['Content-Type'] = settings.JSON_MIME_TYPE
    self.response.write(tojson(r))

  def post(self):
    r = self.jsonpost()
    self.response.headers['Content-Type'] = settings.JSON_MIME_TYPE
    self.response.write(tojson(r))

  def dispatch(self):
    """WSGI request dispatch with automatic JSON parsing."""
    try:
      self.PerformAccessCheck()
    except error.AppError, e:
      # Manually dispatch to handle_exception
      self.handle_exception(e, self.app.debug)
      return

    content_type = self.request.headers.get('Content-Type')
    if content_type and content_type.split(';')[0] == 'application/json':
      self.request.data = json.loads(self.request.body)
    # Exceptions in super.dispatch are automatically routed to handle_exception
    super(AppHandler, self).dispatch()


class ConfigHandler(AppHandler):

  def PerformAccessCheck(self):
    pass

  def jsonget(self):
    map = {
      'your': 'config',
    }
    if not compute.GetAccessToken():
      map['oauth2_url'] = self.MakeOauth2Url()
    return map


class Oauth2Handler(AppHandler):

  def PerformAccessCheck(self):
    assert shared.IsDevMode()

  def jsonpost(self):
    compute.SetAccessToken(access_token=self.request.data['access_token'],
                           token_type=self.request.data['token_type'],
                           expires_in=self.request.data['expires_in'])


class InstanceHandler(AppHandler):

  def PerformAccessCheck(self):
    pass

  def jsonpost(self):
    instance_name = self.user.instance_name
    if not instance_name:
      instance_name = model.AllocateInstance(self.user.key.id())
    return {
      'instance_name': instance_name,
    }


APPLICATION = webapp2.WSGIApplication([
    ('/api/config', ConfigHandler),
    ('/api/oauth2', Oauth2Handler),
    ('/api/instance', InstanceHandler),
], debug=settings.DEBUG)
APPLICATION = middleware.Session(APPLICATION, wsgi_config.WSGI_CONFIG)
APPLICATION = middleware.ErrorHandler(APPLICATION, debug=settings.DEBUG)
