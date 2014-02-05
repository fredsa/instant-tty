import json
import webapp2

from . import settings


_JSON_ENCODER = json.JSONEncoder()
_JSON_ENCODER.indent = 4
_JSON_ENCODER.sort_keys = True

_JSON_DECODER = json.JSONDecoder()


JSON_MIME_TYPE = 'application/json'


def tojson(r):  # pylint:disable-msg=invalid-name
  """Converts a Python object to JSON."""
  return _JSON_ENCODER.encode(r)


def fromjson(json):  # pylint:disable-msg=invalid-name
  """Converts a JSON object into a Python object."""
  if json == '':
    return None
  return _JSON_DECODER.decode(json)


class JsonHandler(webapp2.RequestHandler):
  """Convenience request handler for handler JSON requests and responses."""

  def dispatch(self):
    self.request.data = fromjson(self.request.body)
    r = super(JsonHandler, self).dispatch()
    if self.response.headers['Content-Type'] != settings.JSON_MIME_TYPE:
      self.response.headers['Content-Type'] = settings.JSON_MIME_TYPE
      # JSON Vulnerability Protection, see http://docs.angularjs.org/api/ng.$http
      self.response.write(")]}',\n")
      self.response.write(tojson(r))
