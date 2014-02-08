from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from . import secret
from . import settings
from . import shared
from error import Abort

from google.appengine.api import channel


class Instance(ndb.Model):
  """A Model to store instances."""
  instance_name = ndb.StringProperty(required=True, indexed=True)
  plaintext_secret = ndb.StringProperty(required=True, indexed=False)
  external_ip_addr = ndb.StringProperty(required=False, indexed=False)
  task_name = ndb.StringProperty(required=False, indexed=False)
  user_id = ndb.StringProperty(required=False, indexed=False)


class Instances(ndb.Model):
  """A Model to store all instances."""
  instances = ndb.StructuredProperty(Instance, repeated=True)

INSTANCES_KEY = ndb.Key(Instances, 'bucket-o-thousands')


class User(ndb.Model):
  """A Model to store users."""
  instance_name = ndb.StringProperty(required=False, indexed=True)
  created = ndb.DateTimeProperty(required=True, auto_now_add=True,
                                 indexed=False)
  updated = ndb.DateTimeProperty(required=True, auto_now=True, indexed=False)


def GetOrCreateUser(user_id):
  return User.get_or_insert(user_id)


@ndb.non_transactional
def _MakeInstanceNames(size):
  id_range = Instance.allocate_ids(size=size)
  return ['scratch{}'.format(i) for i in range(id_range[0], id_range[1] + 1)]


@ndb.transactional(xg=True)
def MarkInstanceTaskComplete(instance_name, external_ip_addr):
  # make sure we have a transactionally consistent view
  instances = INSTANCES_KEY.get()

  for instance in instances.instances:
    if instance.instance_name == instance_name:
      assert instance.task_name == shared.GetCurrentTaskName(), 'current task {} unable to access instance {} owned by task {}'.format(shared.GetCurrentTaskName(), instance_name, instance.task_name)
      instance.task_name = None
      instance.external_ip_addr = external_ip_addr
      instances.put()
      return
  shared.w('Unable to find instance {}'.format(instance_name))


def GetInstance(instance_name):
  instances = INSTANCES_KEY.get()
  for instance in instances.instances:
    if instance.instance_name == instance_name:
      return instance
  shared.e('Unable to find instance {}'.format(instance_name))


@ndb.transactional(xg=True)
def AllocateInstance(user_id, instance_ttl_minutes):
  # make sure we have a transactionally consistent view
  user, instances = ndb.get_multi([ndb.Key(User, user_id), INSTANCES_KEY])
  if instances is None:
    instances = Instances(key=INSTANCES_KEY)

  if user.instance_name:
    channel.send_message(user_id, 'User already has instance {}'.format(user.instance_name))
    Abort('User {} already has instance {}'.format(user_id, user.instance_name))

  available_instances = len([instance for instance in instances.instances
                             if instance.user_id is None])
  needed_instances = settings.COMPUTE_IDLE_INSTANCES_TARGET - available_instances + 1
  if needed_instances:
    instance_names = _MakeInstanceNames(needed_instances)
    for instance_name in instance_names:
      plaintext_secret = secret.GenerateRandomString()
      params={
        'instance_name': instance_name,
        'plaintext_secret': plaintext_secret,
      }
      create_task = taskqueue.add(url='/task/create_instance',
                                  queue_name='instances',
                                  transactional=True,
                                  params=params)
      instance = Instance(
        instance_name=instance_name,
        plaintext_secret=plaintext_secret,
        task_name=create_task.name,
        user_id=None,
      )
      delete_task = taskqueue.add(url='/task/delete_instance',
                                  queue_name='instances',
                                  transactional=True,
                                  countdown=instance_ttl_minutes * 60,
                                  params=params)
      instances.instances.append(instance)
    instances.put()

  for instance in instances.instances:
    if instance.user_id is None:
      instance.user_id = user_id
      user.instance_name = instance.instance_name
      ndb.put_multi([user, instances])
      return instance_name

  shared.e('Unexpected')


@ndb.transactional(xg=True)
def DeleteInstance(instance_name):
  instances = INSTANCES_KEY.get()

  for instance in instances.instances:
    if instance.instance_name == instance_name:
      instances.instances.remove(instance)
      instances.put()
      user = ndb.Key(User, instance.user_id).get()
      if user:
        user.instance_name = None
        user.put()
      return

  shared.e('Unable to locate instance {} for user {}'
           .format(instance_name, user_id))


def LookupUser(instance_name, plaintext_secret):
  instances = INSTANCES_KEY.get()
  for instance in instances.Instances:
    if instance.instance_name == instance_name:
      if instance.plaintext_secret != plaintext_secret:
        return None
      return instance.user_id
  return None
