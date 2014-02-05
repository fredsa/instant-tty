import datetime

from google.appengine.api import channel

from . import shared


def create_channel(user_id):
  return channel.create_channel(user_id)


def send_message(user_id, msg):
  # create_channel(user_id)
  msg = '{} {}'.format(datetime.datetime.now(), msg)
  shared.w('send_message({}, {})...'.format(user_id, msg))
  channel.send_message(user_id, msg)
