"""Module containing global playground constants and functions."""

import os

from google.appengine.api import app_identity
from google.appengine.api import backends


DEBUG = True

COMPUTE_IDLE_INSTANCES_TARGET = 1

COMPUTE_PROJECT_ID = app_identity.get_application_id()

COMPUTE_ZONE = 'us-central1-a'

COMPUTE_SCOPE = 'https://www.googleapis.com/auth/compute'

STORAGE_SCOPE_READ_ONLY = 'https://www.googleapis.com/auth/devstorage.read_only'

COMPUTE_MACHINE_TYPE = 'f1-micro'

# whether or not we're running in the dev_appserver
DEV_MODE = os.environ['SERVER_SOFTWARE'].startswith('Development/')

# RFC1113 formatted 'Expires' to prevent HTTP/1.0 caching
LONG_AGO = 'Mon, 01 Jan 1990 00:00:00 GMT'

JSON_MIME_TYPE = 'application/json'

ACCESS_KEY_SET_COOKIE_PARAM_NAME = 'set_access_key_cookie'

ACCESS_KEY_HTTP_HEADER = 'X-App-Access-Key'

ACCESS_KEY_COOKIE_NAME = 'access_key'

ACCESS_KEY_COOKIE_ARGS = {
    'httponly': True,
    'secure': not DEV_MODE,
}

# name for the session cookie
SESSION_COOKIE_NAME = 'session'

SESSION_COOKIE_ARGS = {
    'httponly': True,
    'secure': not DEV_MODE,
}

XSRF_COOKIE_ARGS = {
    'httponly': False,
    'secure': not DEV_MODE,
}

