#!/bin/bash
#
set -eux


time (
  # See https://developers.google.com/compute/docs/instances?hl=en#dmi
  if [ "$( sudo dmidecode -s bios-vendor 2>/dev/null | grep Google )" != "Google" ]
  then
    echo "ERROR: This script must be run on a Google Compute Engine instance."
    exit 1
  fi

  hostname="$( hostname )"
  METADATA_BASE_URL="http://metadata/0.1/meta-data"
  projectid="$( curl --fail --silent $METADATA_BASE_URL/project-id )"
  plaintext_secret="$( curl --fail --silent $METADATA_BASE_URL/attributes/plaintext_secret || echo 'secret42' )"
  agent_base_url="$( curl --fail --silent $METADATA_BASE_URL/attributes/agent_base_url || echo '' )"
  bucket=gs://$projectid

  function send_msg() {
    [ -z "$agent_base_url" ] && return
    msg="$1"
    json="{\"hostname\": \"$hostname\", \"plaintext_secret\": \"$plaintext_secret\", \"msg\": \"$msg\"}"
    curl \
      --fail \
      --silent \
      --header "Content-Type: application/json" \
      --data "$json" \
      $agent_base_url/status \
    || echo "Failed to send msg '$msg'"
  }

  send_msg "Running Compute Engine startup script"

  if [ $(which node >/dev/null; echo $?) != 0 ]
  then
    if [ ! -d node-v0.10.24-linux-x64 ]
    then
      send_msg "Downloading Node.js"
      curl --silent http://nodejs.org/dist/v0.10.24/node-v0.10.24-linux-x64.tar.gz | tar xz
    fi

    export PATH="$(pwd)/node-v0.10.24-linux-x64/bin:$PATH"
  fi

  if [ ! -d instant-tty ]
  then
    if [ $( gsutil -q stat $bucket/instant-tty.tar.gz ;echo $? ) == 0 ]
    then
      send_msg "Using existing pre-built project archive $bucket/instant-tty.tar.gz ..."
      gsutil -q cp $bucket/instant-tty.tar.gz .
      tar xfz instant-tty.tar.gz
    else
      send_msg "Updating package database"
      sudo apt-get update -y

      send_msg "Installing git"
      sudo apt-get install -y git

      send_msg "Cloning git repo"
      git clone https://github.com/fredsa/instant-tty

      send_msg "Creating and uploading new archive $bucket/instant-tty.tar.gz"
      tar cfz instant-tty.tar.gz instant-tty/
      gsutil -q cp instant-tty.tar.gz $bucket/instant-tty.tar.gz \
        && gsutil -q ls -la $bucket/instant-tty.tar.gz \
        || echo "WARNING: Unable to write to $bucket/instant-tty.tar.gz"
    fi

    if [ $( gsutil -q stat $bucket/node_modules.tar.gz ;echo $? ) == 0 ]
    then
      send_msg "Using existing pre-built node_modules archive $bucket/node_modules.tar.gz ..."
      gsutil -q cp $bucket/node_modules.tar.gz .
      tar xfz node_modules.tar.gz
    else
      send_msg "Installing make / g++"
      sudo apt-get install -y make g++

      send_msg "Building a new node_modules archive ..."
      (
        send_msg "Running 'npm install'"
        cd instant-tty/term
        npm install
      )
      tar cfz node_modules.tar.gz instant-tty/term/node_modules/
      gsutil -q cp node_modules.tar.gz $bucket/node_modules.tar.gz \
        && gsutil -q ls -la $bucket/node_modules.tar.gz \
        || echo "WARNING: Unable to write to $bucket/node_modules.tar.gz"
    fi
  fi

  send_msg "Launching tty server..."
  (
    cd instant-tty
    scripts/term.sh --secret "$plaintext_secret" --port 80 -d
    send_msg "SERVER_READY"
  )
)
