import httplib
import shared
import webapp2

from . import compute
from . import model
from . import settings

class InstanceHandler(webapp2.RequestHandler):

  def post(self):
    instance_name = self.request.get('instance_name')
    plaintext_secret = self.request.get('plaintext_secret')
    assert instance_name
    assert plaintext_secret
    # TODO: Make sure we don't re-use an undeleted disk
    disk_name = compute.GetOrCreateDisk(instance_name)
    if not disk_name:
      self.error(httplib.REQUEST_TIMEOUT)
      return
    metadata = {
      'plaintext_secret': plaintext_secret,
    }
    instance_name = compute.GetOrCreateInstance(instance_name, metadata)
    if not instance_name:
      self.error(httplib.REQUEST_TIMEOUT)
      return
    model.MarkInstanceTaskComplete(instance_name)


APPLICATION = webapp2.WSGIApplication([
    ('/task/instance', InstanceHandler),
], debug=settings.DEBUG)
