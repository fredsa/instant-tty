import webapp2

from google.appengine.api import app_identity
from google.appengine.api import channel

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
    # plaintext_secret = self.request.data['plaintext_secret']
    user_id = self.request.data['user_id']
    msg = self.request.data['msg']
    channel.send_message(user_id, msg)


APPLICATION = webapp2.WSGIApplication([
    ('/agent/status', StatusHandler),
], debug=settings.DEBUG)
APPLICATION = middleware.PlaintextSecretExtractor(APPLICATION)
APPLICATION = middleware.ErrorHandler(APPLICATION, debug=settings.DEBUG)
