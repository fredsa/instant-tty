#!/bin/bash
#
set -eux

SCRIPTS_DIR=$( dirname $0 )
ROOT_DIR=$( dirname $SCRIPTS_DIR )

plaintext_secret="secret42"

if [ "$#" -ge 2 ]
  then
  if [ "$1" == "--secret" ]
  then
    shift
    plaintext_secret="$1"
    shift
  fi
fi
(
  cd $ROOT_DIR/term
  sed -i -e "s/\(resource.*\)'socket.io'/\1'$plaintext_secret'/" node_modules/tty.js/static/tty.js
  sed -i -e "s/secret42/$plaintext_secret/" index.js
  ./index.js $*
)
