#!/bin/bash
#
set -evu

cd

if [ $(which git >/dev/null; echo $?) == 1 ]
then
  sudo apt-get update -y
  sudo apt-get install -y git make g++
fi

if [ ! -d node-v0.10.24-linux-x64 ]
then
  wget http://nodejs.org/dist/v0.10.24/node-v0.10.24-linux-x64.tar.gz
  tar xvfz node-v0.10.24-linux-x64.tar.gz
fi
export PATH=$PATH:~/node-v0.10.24-linux-x64/bin

if [ ! -d instant-tty ]
then
  git clone https://github.com/fredsa/instant-tty
fi

cd instant-tty

if [ ! -d node_modules ]
then
  npm install
fi

sed -i -e "s/\(resource.*\)'socket.io'/\1'secret42'/" node_modules/tty.js/static/tty.js

./index.js
