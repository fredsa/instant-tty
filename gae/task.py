import httplib
import shared
import webapp2

from . import agent
from . import compute
from . import model
from . import settings


class CreateInstanceHandler(webapp2.RequestHandler):

  def post(self):
    instance_name = self.request.get('instance_name')
    assert instance_name
    plaintext_secret = self.request.get('plaintext_secret')
    assert plaintext_secret
    # TODO: Make sure we don't re-use an undeleted disk
    disk_name = compute.GetOrCreateDisk(instance_name)
    if not disk_name:
      self.error(httplib.REQUEST_TIMEOUT)
      return
    metadata = {
      'agent_base_url': agent.GetAgentBaseUrl(),
      'plaintext_secret': plaintext_secret,
    }
    instance = compute.GetOrCreateInstance(instance_name, metadata)
    if not instance or instance['status'] != 'RUNNING':
      self.error(httplib.REQUEST_TIMEOUT)
      return
    networkInterfaces = instance['networkInterfaces']
    accessConfigs = networkInterfaces[0]['accessConfigs']
    external_ip_addr = accessConfigs[0]['natIP']
    model.MarkInstanceTaskComplete(instance_name,
                                   external_ip_addr=external_ip_addr)


class DeleteInstanceHandler(webapp2.RequestHandler):

  def post(self):
    instance_name = self.request.get('instance_name')
    assert instance_name
    plaintext_secret = self.request.get('plaintext_secret')
    assert plaintext_secret
    compute.DeleteInstanceIfExists(instance_name)
    compute.DeleteDiskIfExists(instance_name)
    model.DeleteInstance(instance_name)


APPLICATION = webapp2.WSGIApplication([
    ('/task/create_instance', CreateInstanceHandler),
    ('/task/delete_instance', DeleteInstanceHandler),
], debug=settings.DEBUG)
