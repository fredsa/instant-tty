import httplib
import shared
import webapp2

from . import compute
from . import model
from . import settings

class InstanceHandler(webapp2.RequestHandler):

  def post(self):
    instance_name = self.request.get('instance_name')
    assert instance_name
    disk_name = compute.GetOrCreateDisk(instance_name)
    if not disk_name:
      self.error(httplib.REQUEST_TIMEOUT)
      return
    instance_name = compute.GetOrCreateInstance(instance_name)
    if not instance_name:
      self.error(httplib.REQUEST_TIMEOUT)
      return
    model.MarkInstanceTaskComplete(instance_name)


APPLICATION = webapp2.WSGIApplication([
    ('/task/instance', InstanceHandler),
], debug=settings.DEBUG)
