#!/bin/bash
#
set -euv

time (
  # See https://developers.google.com/compute/docs/instances?hl=en#dmi
  if [ "$( sudo dmidecode -s bios-vendor 2>/dev/null | grep Google )" != "Google" ]
  then
    echo "ERROR: This script must be run on a Google Compute Engine instance."
    exit 1
  fi

  projectid="$( curl -s http://metadata/0.1/meta-data/project-id )"
  gsfile=gs://$projectid/instant-tty.zip

  if [ $(which git >/dev/null; echo $?) != 0 ]
  then
    # sudo apt-get update -y
    sudo apt-get install -y git make g++ zip
  fi

  if [ $(which node >/dev/null; echo $?) != 0 ]
  then
    if [ ! -d node-v0.10.24-linux-x64 ]
    then
      curl --silent http://nodejs.org/dist/v0.10.24/node-v0.10.24-linux-x64.tar.gz | tar xz
    fi

    export PATH="$(pwd)/node-v0.10.24-linux-x64/bin:$PATH"
  fi

  if [ ! -d instant-tty ]
  then
    if [ $( gsutil -q stat $gsfile ;echo $? ) == 0 ]
    then
      echo "Using existing pre-built project archive $gsfile ..."
      gsutil -q cp $gsfile .
      unzip -q instant-tty.zip
    else
      echo "Building a new project archive, which we will attempt to copy to $gsfile ..."
      git clone https://github.com/fredsa/instant-tty
      (
        cd instant-tty
        npm install
        sed -i -e "s/\(resource.*\)'socket.io'/\1'secret42'/" node_modules/tty.js/static/tty.js
      )
      zip --quiet -r instant-tty instant-tty/
      gsutil -q cp instant-tty.zip $gsfile
      gsutil -q ls -la $gsfile
    fi
  fi


  echo "Launching server..."
  (
    cd instant-tty
    ./index.js --port 80
  )
)
