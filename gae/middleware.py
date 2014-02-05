"""App middleware."""

import httplib
import logging
import sys

import webapp2
from webapp2_extras import securecookie
from webapp2_extras import security
from webapp2_extras import sessions

from . import error
from error import Abort
from . import model
from . import settings
from . import shared

from google.appengine.api import users


# session key to store the anonymous user object
_ANON_USER_KEY = u'anon_user_key'

# AngularJS XSRF Cookie, see http://docs.angularjs.org/api/ng.$http
_XSRF_TOKEN_COOKIE = 'XSRF-TOKEN'

# AngularJS XSRF HTTP Header, see http://docs.angularjs.org/api/ng.$http
_XSRF_TOKEN_HEADER = 'HTTP_X_XSRF_TOKEN'


def MakeCookieHeader(name, value, cookie_args=None):
  items = ['{}={}'.format(name, value)]
  items.append('Path=/')
  if cookie_args:
    if cookie_args['secure']:
      items.append('secure')
    if cookie_args['httponly']:
      items.append('HttpOnly')
  cookie_header = ('set-cookie', '; '.join(items))
  return cookie_header


# TODO: use datastore sequence instead
def MakeAnonUserKey():
  suffix = security.generate_random_string(
      length=10,
      pool=security.LOWERCASE_ALPHANUMERIC)
  return 'user_{0}'.format(suffix)


def AdoptAnonymousProjects(dest_user_key, source_user_key):
  model.AdoptProjects(dest_user_key, source_user_key)


def GetOrMakeSession(request):
  """Get a new or current session."""
  session_store = sessions.get_store(request=request)
  session = session_store.get_session()

  if not session:
    session['xsrf'] = security.generate_random_string(entropy=128)
  user = users.get_current_user()
  if user:
    if _ANON_USER_KEY in session:
      AdoptAnonymousProjects(user.email(), session[_ANON_USER_KEY])
      del session[_ANON_USER_KEY]
  else:
    if _ANON_USER_KEY not in session:
      session[_ANON_USER_KEY] = MakeAnonUserKey()

  return session


def GetUserKey(session):
  """Returns the email from logged in user or the session user key."""
  user = users.get_current_user()
  if user:
    return user.email()
  return session[_ANON_USER_KEY]


def _PerformCsrfRequestValidation(session, environ):
  session_xsrf = session['xsrf']
  client_xsrf = environ.get(_XSRF_TOKEN_HEADER)
  if not client_xsrf:
    Abort(httplib.UNAUTHORIZED, 'Missing client XSRF token.')
  if client_xsrf != session_xsrf:
    # do not log tokens in production
    if shared.IsDevMode():
      logging.error('Client XSRF token={0!r}, session XSRF token={1!r}'
                    .format(client_xsrf, session_xsrf))
    Abort(httplib.UNAUTHORIZED,
          'Client XSRF token does not match session XSRF token.')


class Session(object):
  """WSGI middleware which adds user/project sessions.

  Adds the following keys to the environ:
  - environ['app.session'] contains a webapp2 session
  - environ['app.user']    contains the current user entity
  """

  def __init__(self, app, config):
    self.app = app
    self.app.config = webapp2.Config(config)
    secret_key = config['webapp2_extras.sessions']['secret_key']
    self.serializer = securecookie.SecureCookieSerializer(secret_key)

  def MakeSessionCookieHeader(self, session):
    value = self.serializer.serialize(settings.SESSION_COOKIE_NAME,
                                      dict(session))
    value = '"{}"'.format(value)
    return MakeCookieHeader(settings.SESSION_COOKIE_NAME, value,
                            settings.SESSION_COOKIE_ARGS)

  def MakeXsrfCookieHeader(self, session):
    return MakeCookieHeader(_XSRF_TOKEN_COOKIE, session['xsrf'],
                            settings.XSRF_COOKIE_ARGS)

  def __call__(self, environ, start_response):
    additional_headers = []

    # pylint:disable-msg=invalid-name
    def custom_start_response(status, headers, exc_info=None):
      headers.extend(additional_headers)
      # keep session cookies private
      headers.extend([
          # Note App Engine automatically sets a 'Date' header for us. See
          # https://developers.google.com/appengine/docs/python/runtime#Responses
          ('Expires', settings.LONG_AGO),
          ('Cache-Control', 'private, max-age=0'),
      ])
      return start_response(status, headers, exc_info)

    # 1. ensure we have a session
    request = webapp2.Request(environ, app=self.app)
    session = environ['app.session'] = GetOrMakeSession(request)

    if session.modified:
      additional_headers.extend([
          self.MakeSessionCookieHeader(session),
          self.MakeXsrfCookieHeader(session),
      ])

    # 2. ensure we have an user entity
    user_key = GetUserKey(session)
    assert user_key
    # TODO: avoid creating a datastore entity on every anonymous request
    environ['app.user'] = model.GetOrCreateUser(user_key)

    # 3. perform CSRF checks
    if not shared.IsHttpReadMethod(environ):
      _PerformCsrfRequestValidation(session, environ)

    return self.app(environ, custom_start_response)


class PlaintextSecretExtractor(object):
  """WSGI middleware which extracts plaintext secrets.
  """

  def __init__(self, app):
    self.app = app

  def __call__(self, environ, start_response):
    request = webapp2.Request(environ, app=self.app)
    plaintext_secret = request.get('plaintext_secret')
    if plaintext_secret:
      environ['plaintext_secret'] = 'plaintext_secret'
    return self.app(environ, start_response)


class ErrorHandler(object):
  """WSGI middleware which adds AppError handling."""

  def __init__(self, app, debug):
    self.app = app
    self.debug = debug

  def __call__(self, environ, start_response):
    if shared.IsDevMode():
      logging.info('\n' * 1)
    try:
      return self.app(environ, start_response)
    except Exception, e:  # pylint:disable-msg=broad-except
      status, headers, body = error.MakeErrorResponse(e, self.debug)
      start_response(status, headers, sys.exc_info())
      return body
