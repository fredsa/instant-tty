import cgi
import httplib
import webapp2

from . import channel
from . import compute
from . import error
from . import middleware
from . import model
from . import settings
from . import shared
from . import wsgi_config

from error import Abort

from google.appengine.api import app_identity
from google.appengine.api import urlfetch


# From https://cloud.google.com/console/project/apps~little-black-box/apiui/credential
CLIENT_ID = '638064416490.apps.googleusercontent.com'

# TODO: create redirect URI dynamically
if shared.IsDevMode():
  redirect_uri = 'http://localhost:8080/'
else:
  redirect_uri = 'https://{}/'.format(app_identity.get_default_version_hostname())


class AppHandler(shared.AccessCheckHandler):
  """Convenience request handler with app specific functionality."""

  @webapp2.cached_property
  def user(self):
    return self.request.environ['app.user']

  @webapp2.cached_property
  def user_id(self):
    return self.user.key.id()

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


class ConfigHandler(AppHandler):

  def PerformAccessCheck(self):
    pass

  def get(self):
    map = {
      'user_id': self.user_id,
      'channel_token': channel.create_channel(self.user_id),
    }
    if shared.IsDevMode() and not compute.GetDevModeAccessToken():
      map['oauth2_url'] = self.MakeOauth2Url()
    return map


class Oauth2Handler(AppHandler):

  def PerformAccessCheck(self):
    assert shared.IsDevMode()

  def post(self):
    compute.SetDevModeAccessToken(access_token=self.request.data['access_token'],
                                  token_type=self.request.data['token_type'],
                                  expires_in=self.request.data['expires_in'])


class InstanceHandler(AppHandler):

  def PerformAccessCheck(self):
    pass

  def post(self):
    instance_name = self.user.instance_name
    if not self.user.instance_name:
      channel.send_message(self.user_id, 'Allocating instance ...')
      instance_name = model.AllocateInstance(self.user_id,
                                             settings.COMPUTE_INSTANCE_TTL_MINUTES)
    instance = model.GetInstance(instance_name)
    if instance.task_name:
      Abort(httplib.REQUEST_TIMEOUT, 'Waiting on provisioning task {}'
                                     .format(instance.task_name))
    try:
      response = urlfetch.fetch(url='http://{}'.format(instance.external_ip_addr),
                                follow_redirects=False)
      if response.status_code != httplib.OK:
        Abort(httplib.REQUEST_TIMEOUT,
              'Waiting for instance startup script to complete: {}'
              .format(response.status_code))
    except urlfetch.DownloadError, e:
      Abort(httplib.REQUEST_TIMEOUT,
            'Waiting for instance startup script to complete: {}'
            .format(e))
    return {
      'instance_name': instance.instance_name,
      'external_ip_addr': instance.external_ip_addr,
    }


APPLICATION = webapp2.WSGIApplication([
    ('/api/config', ConfigHandler),
    ('/api/oauth2', Oauth2Handler),
    ('/api/instance', InstanceHandler),
], debug=settings.DEBUG)
APPLICATION = middleware.Session(APPLICATION, wsgi_config.WSGI_CONFIG)
APPLICATION = middleware.ErrorHandler(APPLICATION, debug=settings.DEBUG)
