#!/bin/bash
#
set -eux

sed -i -e "s/\(resource.*\)'socket.io'/\1'secret42'/" term/node_modules/tty.js/static/tty.js
term/index.js $*
