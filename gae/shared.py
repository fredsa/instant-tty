"""Module for shared playground functions."""

import httplib
import logging
import os

from error import Abort
from . import jsonutil
from . import settings

from google.appengine.api import app_identity
from google.appengine.api import backends
from google.appengine.api import users
from google.appengine.api import urlfetch


URL_FETCH_DEADLINE = 3

# HTTP methods which do not affect state
HTTP_READ_METHODS = ('GET', 'OPTIONS')


def e(msg, *args, **kwargs):  # pylint:disable-msg=invalid-name
  if isinstance(msg, basestring):
    if args or kwargs:
      msg = msg.format(*args, **kwargs)
  raise RuntimeError(repr(msg))


def i(msg, *args, **kwargs):  # pylint:disable-msg=invalid-name
  if isinstance(msg, basestring):
    if args or kwargs:
      msg = msg.format(*args, **kwargs)
  logging.info('@@@@@ {0}'.format(repr(msg)))


def w(msg, *args, **kwargs):  # pylint:disable-msg=invalid-name
  if isinstance(msg, basestring):
    if args or kwargs:
      msg = msg.format(*args, **kwargs)
  logging.warning('##### {0}'.format(repr(msg)))


def IsDevMode():
  return settings.DEV_MODE


def Fetch(access_key, url, method, payload=None, deadline=URL_FETCH_DEADLINE,
          retries=1):
  for i in range(0, retries):
    try:
      headers = {settings.ACCESS_KEY_HTTP_HEADER: access_key}
      return urlfetch.fetch(url, headers=headers, method=method,
                            payload=payload, follow_redirects=False,
                            deadline=deadline)
    except Exception, e:
      if i == retries - 1:
        raise
      w('Will retry {} {} which encountered {}'.format(method, url, e))


def GetCurrentTaskName():
  return os.environ.get('HTTP_X_APPENGINE_TASKNAME')


def EnsureRunningInTask():
  """Ensures that we're currently executing inside a task.

  Raises:
    RuntimeError: when not executing inside a task.
  """
  if GetCurrentTaskName():
    return
  raise RuntimeError('Not executing in a task queue')


def IsHttpReadMethod(environ):
  return environ['REQUEST_METHOD'] in HTTP_READ_METHODS


def AssertIsAdmin():
  if not users.is_current_user_admin():
    Abort(403, 'Admin only function')


class AccessCheckHandler(jsonutil.JsonHandler):
  """Convenience request handler for handler JSON requests and responses."""

  def PerformAccessCheck(self):
    """Perform authorization checks.

    Subclasses must provide a suitable implementation.

    Raises:
      error.AppError if autorization check fails
    """
    raise NotImplementedError()

  def dispatch(self):
    """WSGI request dispatch with automatic JSON handling and access checks."""
    try:
      self.PerformAccessCheck()
    except error.AppError, e:
      # Manually dispatch to handle_exception
      self.handle_exception(e, self.app.debug)
      return

    content_type = self.request.headers.get('Content-Type')
    if content_type and content_type.split(';')[0] == settings.JSON_MIME_TYPE:
      self.request.data = jsonutil.fromjson(self.request.body)
    # Exceptions in super.dispatch are automatically routed to handle_exception
    super(AccessCheckHandler, self).dispatch()
