#!/bin/bash
#
set -eux

plaintext_secret="secret42"

if [ "$#" -ge 2 ]
  if [ "$1" == "--secret" ]
  then
    shift
    plaintext_secret="$2"
    shift
  fi
fi
sed -i -e "s/\(resource.*\)'socket.io'/\1'$plaintext_secret'/" term/node_modules/tty.js/static/tty.js
term/index.js $*
