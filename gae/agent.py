import webapp2

from google.appengine.api import app_identity

from . import channel
from . import settings
from . import shared
from . import middleware


def GetAgentBaseUrl():
  return ('https://{}/agent'.format(app_identity.get_default_version_hostname()))


class AgentHandler(shared.AccessCheckHandler):
  """Convenience request handler with app specific functionality."""
  pass


class StatusHandler(AgentHandler):

  def PerformAccessCheck(self):
    pass

  def post(self):
    # TODO: confirm plaintext_secret
    instance_name = self.request.data['hostname']
    assert instance_name
    plaintext_secret = self.request.data['plaintext_secret']
    assert plaintext_secret
    msg = self.request.data['msg']
    assert msg
    user_id = model.LookupUser(instance_name, plaintext_secret)
    if user_id is None:
      Abort(httplib.NOT_FOUND,
            'Failed to lookup user_id from instance {} with plaintext secret {}'
            .format(instance_name, plaintext_secret))
    channel.send_message(user_id, msg)


APPLICATION = webapp2.WSGIApplication([
    ('/agent/status', StatusHandler),
], debug=settings.DEBUG)
APPLICATION = middleware.PlaintextSecretExtractor(APPLICATION)
APPLICATION = middleware.ErrorHandler(APPLICATION, debug=settings.DEBUG)
