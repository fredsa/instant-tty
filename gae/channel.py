import datetime

from google.appengine.api import channel

from . import shared


def create_channel(client_id):
  return channel.create_channel(client_id)


def send_message(client_id, msg):
  msg = '{} {}'.format(datetime.datetime.now(), msg)
  shared.i('Sending msg to {}: {}'.format(client_id, msg))
  channel.send_message(client_id, msg)
