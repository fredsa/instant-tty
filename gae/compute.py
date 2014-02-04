import httplib
import logging
import json
import os
import shared

from google.appengine.api import app_identity
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from . import settings

from error import Abort


COMPUTE_BASE_URL = 'https://www.googleapis.com/compute/v1'

COMPUTE_PROJECT_ZONE_URL = ('{}/projects/{}/zones/{}'
                            .format(COMPUTE_BASE_URL,
                                    settings.COMPUTE_PROJECT_ID,
                                    settings.COMPUTE_ZONE))

COMPUTE_PROJECT_GLOBAL_URL = ('https://www.googleapis.com/compute/v1'
                              '/projects/{}/global'
                              .format(settings.COMPUTE_PROJECT_ID))

COMPUTE_MACHINE_TYPE_URL = ('{}/machineTypes/{}'
                            .format(COMPUTE_PROJECT_ZONE_URL,
                                    settings.COMPUTE_MACHINE_TYPE))

COMPUTE_INSTANCES_URL = '{}/instances'.format(COMPUTE_PROJECT_ZONE_URL)

DEBBIAN_CLOUD_PROJECT = 'debian-cloud'

DEBIAN_CLOUD_IMAGES_URL = ('{}/projects/{}/global/images'
                           .format(COMPUTE_BASE_URL,
                                   DEBBIAN_CLOUD_PROJECT))

COMPUTE_DISKS_URL = '{}/disks'.format(COMPUTE_PROJECT_ZONE_URL)

DEFAULT_NETWORK_URL = '{}/networks/default'.format(COMPUTE_PROJECT_GLOBAL_URL)

COMPUTE_AUTHORIZATION_MEMCACHE_KEY = 'COMPUTE_AUTHORIZATION_MEMCACHE_KEY'

STARTUP_SCRIPT_URL='https://raw.github.com/fredsa/instant-tty/master/compute-startup.sh'


def _Fetch(reason, url, method='GET', payload=None):
  if shared.IsDevMode():
    authorization_value = GetDevModeAccessToken()
  else:
    Authorization_token, _ = app_identity.get_access_token(settings.COMPUTE_SCOPE)
    authorization_value = 'OAuth {}'.format(Authorization_token)
  assert authorization_value
  response = urlfetch.fetch(url=url,
                            method=method,
                            payload=payload,
                            follow_redirects=False,
                            headers = {
                              'Content-Type': settings.JSON_MIME_TYPE,
                              'Authorization': authorization_value,
                            })
  shared.i('COMPUTE: {} -> {}'.format(reason, httplib.responses[response.status_code]))

  if response.status_code != 200:
    Abort(response.status_code, 'UrlFetch() {} {}\nWith Payload: {}\nResulted in:\n{}'
                                .format(method, url, payload, response.content))
  return json.loads(response.content)

def GetDevModeAccessToken():
  access_token = memcache.get(COMPUTE_AUTHORIZATION_MEMCACHE_KEY)
  # shared.w('{} <- GetDevModeAccessToken()'.format(access_token))
  return access_token


def SetDevModeAccessToken(access_token, token_type, expires_in):
  # shared.w('SetDevModeAccessToken({})'.format(access_token))
  memcache.set(COMPUTE_AUTHORIZATION_MEMCACHE_KEY,
               '{} {}'.format(token_type, access_token))


def ListInstances():
  r = _Fetch('LIST INSTANCES',url=COMPUTE_INSTANCES_URL)
  return [item['name'] for item in r['items']]


# TODO: Replace with 'filter'
def _IsDesiredImage(image):
  if image.get('deprecated'):
    return False
  if not image['name'].startswith('debian'):
    return False
  return True


def ListDebianCloudImages():
  r = _Fetch('images.list(debian && !deprecated)',
             url=DEBIAN_CLOUD_IMAGES_URL)
  return [item['selfLink'] for item in r['items'] if _IsDesiredImage(item)]


def CreateDisk(user_id, disk_name):
  imageurl = ListDebianCloudImages()[0]
  url = '{}?sourceImage={}'.format(COMPUTE_DISKS_URL, imageurl)
  r = _Fetch('disks.create({!r})'.format(disk_name),
             url=url,
             method='POST',
             payload=json.dumps({
               'name': disk_name,
             }))
  return r


def _GetDisk(user_id, disk_name):
  url = '{}/{}'.format(COMPUTE_DISKS_URL, disk_name)
  r = _Fetch('disks.get({!r})'.format(disk_name), url=url)
  return r


def GetOrCreateDisk(user_id, disk_name):
  try:
    disk = _GetDisk(user_id, disk_name)
    return disk
  except:
    disk = CreateDisk(user_id, disk_name)
    return None


def GetInstance(user_id, instance_name):
  url = '{}/{}'.format(COMPUTE_INSTANCES_URL, instance_name)
  r = _Fetch('instances.get({!r})'.format(instance_name), url=url)
  return r


def _CreateInstance(user_id, instance_name, metadata=None):
  metadata = metadata or {}
  metadata['startup-script-url'] = STARTUP_SCRIPT_URL
  metadata_items = [{'key': k, 'value': v} for k,v in metadata.iteritems()]
  disk = GetOrCreateDisk(user_id, instance_name)
  diskurl = disk['selfLink']
  payload = json.dumps({
   'machineType': COMPUTE_MACHINE_TYPE_URL,
   'name': instance_name,
   'networkInterfaces': [{
     'accessConfigs': [{
       'type': 'ONE_TO_ONE_NAT',
       'name': 'External NAT'
     }],
     'network': DEFAULT_NETWORK_URL,
   }],
   'disks': [{
     'boot': True,
     'type': 'PERSISTENT',
     'mode': 'READ_WRITE',
     'deviceName': instance_name,
     'source': diskurl,
   }],
   'metadata': {
     'items': metadata_items,
   },
   'serviceAccounts': [
     {
       'email': 'default',
       'scopes': [
         settings.STORAGE_SCOPE_READ_ONLY
       ]
     }
   ],
  })
  r = _Fetch('instances.insert({!r})'.format(instance_name),
             url=COMPUTE_INSTANCES_URL,
             method='POST',
             payload=payload)
  return r

def GetOrCreateInstance(user_id, instance_name, metadata):
  try:
    instance = GetInstance(user_id, instance_name)
  except:
    operation = _CreateInstance(user_id, instance_name, metadata)
    instance = GetInstance(user_id, instance_name)
  return instance


