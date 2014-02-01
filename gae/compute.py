import httplib
import logging
import json
import os
import shared

from google.appengine.api import app_identity
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


def _Fetch(reason, url, method='GET', payload=None):
  if shared.IsDevMode():
    import devmode
    authorization_token = devmode.authorization_token
  else:
    authorization_token, _ = app_identity.get_access_token(settings.COMPUTE_SCOPE)
  response = urlfetch.fetch(url=url,
                            method=method,
                            payload=payload,
                            follow_redirects=False,
                            headers = {
                              'Content-Type': settings.JSON_MIME_TYPE,
                              'Authorization': 'OAuth ' + authorization_token
                            })
  shared.i('COMPUTE: {} -> {}'.format(reason, httplib.responses[response.status_code]))

  if response.status_code != 200:
    Abort(response.status_code, 'UrlFetch() {} {}\nWith Payload: {}\nResulted in:\n{}'
                                .format(method, url, payload, response.content))
  return json.loads(response.content)

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


def CreateDisk(disk_name):
  imageurl = ListDebianCloudImages()[0]
  url = '{}?sourceImage={}'.format(COMPUTE_DISKS_URL, imageurl)
  r = _Fetch('disks.create({!r})'.format(disk_name),
             url=url,
             method='POST',
             payload=json.dumps({
               'name': disk_name,
             }))
  return r


def _GetDisk(disk_name):
  url = '{}/{}'.format(COMPUTE_DISKS_URL, disk_name)
  r = _Fetch('disks.get({!r})'.format(disk_name), url=url)
  return r


def GetOrCreateDisk(disk_name):
  try:
    disk = _GetDisk(disk_name)
    return disk
  except:
    disk = CreateDisk(disk_name)
    return None


def GetInstance(instance_name):
  url = '{}/{}'.format(COMPUTE_INSTANCES_URL, instance_name)
  r = _Fetch('instances.get({!r})'.format(instance_name), url=url)
  return r


def _CreateInstance(instance_name):
  disk = GetOrCreateDisk(instance_name)
  diskurl = disk['selfLink']
  r = _Fetch('instances.insert({!r})'.format(instance_name),
             url=COMPUTE_INSTANCES_URL,
             method='POST',
             payload=json.dumps({
               'machineType': COMPUTE_MACHINE_TYPE_URL,
               'name': instance_name,
               'networkInterfaces': [{
                 'network': DEFAULT_NETWORK_URL,
               }],
               'disks': [{
                 'boot': True,
                 'type': 'PERSISTENT',
                 'source': diskurl,
               }],
             }))
  return r

def GetOrCreateInstance(instance_name):
  try:
    instance = GetInstance(instance_name)
    return instance_name
  except:
    instance = _CreateInstance(instance_name)
    return None


