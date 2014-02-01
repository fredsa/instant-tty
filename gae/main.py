import cgi
import json
import webapp2

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
    return {
      'your': 'config'
    }


class InstanceHandler(AppHandler):

  def PerformAccessCheck(self):
    pass

  def jsonpost(self):
    # import compute; compute.GetOrCreateInstance('xyz'); return {'instance_name': 'xyz'}

    instance_name = self.user.instance_name
    if not instance_name:
      instance_name = model.AllocateInstance(self.user.key.id())
    return {
      'instance_name': instance_name,
    }


APPLICATION = webapp2.WSGIApplication([
    ('/api/config', ConfigHandler),
    ('/api/instance', InstanceHandler),
], debug=settings.DEBUG)
APPLICATION = middleware.Session(APPLICATION, wsgi_config.WSGI_CONFIG)
APPLICATION = middleware.ErrorHandler(APPLICATION, debug=settings.DEBUG)
