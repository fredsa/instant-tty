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

  METADATA_BASE_URL="http://metadata/0.1/meta-data"
  projectid="$( curl --fail --silent $METADATA_BASE_URL/project-id )"
  user_id="$( curl --fail --silent $METADATA_BASE_URL/attributes/user_id || echo 'nobody' )"
  plaintext_secret="$( curl --fail --silent $METADATA_BASE_URL/attributes/plaintext_secret || echo 'secret42' )"
  agent_base_url="$( curl --fail --silent $METADATA_BASE_URL/attributes/agent_base_url || echo '' )"
  gsfile=gs://$projectid/instant-tty.tar.gz

  function send_msg() {
    [ -z "$agent_base_url" ] && return
    msg="$1"
    json="{\"user_id\": \"$user_id\", \"plaintext_secret\": \"$plaintext_secret\", \"msg\": \"$msg\"}"
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
    if [ $( gsutil -q stat $gsfile ;echo $? ) == 0 ]
    then
      send_msg "Using existing pre-built project archive $gsfile ..."
      gsutil -q cp $gsfile .
      tar xfz instant-tty.tar.gz
    else
      send_msg "Building a new project archive, which we will attempt to copy to $gsfile ..."

      send_msg "Updating package database"
      sudo apt-get update -y

      send_msg "Installing packages"
      sudo apt-get install -y git make g++

      send_msg "Cloning git repo"
      git clone https://github.com/fredsa/instant-tty
      (
        send_msg "Running 'npm install'"
        cd instant-tty/term
        npm install
      )
      send_msg "Creating and uploading new archive $gsfile"
      tar cfz instant-tty.tar.gz instant-tty/
      gsutil -q cp instant-tty.tar.gz $gsfile && gsutil -q ls -la $gsfile || echo "WARNING: Unable to write to $gsfile"
    fi
  fi


  send_msg "Launching tty server..."
  (
    cd instant-tty
    ./term.sh --secret "$plaintext_secret" --port 80 -d
    send_msg "SERVER_READY"
  )
)
