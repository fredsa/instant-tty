#!/bin/bash
#
set -eu

if [ $# == 2 ]
then
  projectid="$1"
  shift
fi

if [ $# == 0 ]
then
  echo ""
  echo "Usage:"
  echo "  $0 [projectid] <instance-name>"
  echo ""
  exit 1
fi

gsfile="gs://$projectid/instant-tty.tar.gz"
if [ $( gsutil -q stat $gsfile; echo $? ) == 0 ]
then
  scopes=storage-ro
else
  scopes=storage-rw
fi

instancename="$1"
shift

ZONE=us-central1-a
MACHINE_TYPE=f1-micro
IMAGE=$(
  # select the most recent debian-* image
  gcutil listimages \
    --project=google \
    --filter 'description ne .*DEPRECATED.*' \
    --filter 'name eq debian-.*' \
    --format=names \
  | sort -n \
  | tail -1)
STARTUP_SCRIPT_URL=https://raw.github.com/fredsa/instant-tty/master/compute-startup.sh

echo "EXISTING INSTANCES: "
gcutil listinstances \
  --zone $ZONE \
  --project $projectid

echo ""
echo "READY TO CREATE NEW INSTANCE:"
echo "  Project id            : $projectid"
echo "  Instance name         : $instancename"
echo "  Zone                  : $ZONE"
echo "  Image                 : $IMAGE"
echo "  Machine type          : $MACHINE_TYPE"
echo "  Startup script URL    : $STARTUP_SCRIPT_URL"
echo "  Startup archive       : $gsfile"
echo "  Service account scopes: $scopes"
echo ""
echo -e "Hit [ENTER] to confirm: \c"
read dummy

# Ensure that we have a firewall rule in place
gcutil getfirewall allow-inbound-http >/dev/null \
  --project $projectid ||
gcutil addfirewall allow-inbound-http \
  --allowed="tcp:80" \
  --description "Incoming HTTP allowed" \
  --project=$projectid

# Create instance
gcutil addinstance $instancename \
  --machine_type $MACHINE_TYPE \
  --image $IMAGE \
  --metadata="startup-script-url:$STARTUP_SCRIPT_URL" \
  --service_account_scopes=$scopes \
  --zone $ZONE \
  --project $projectid

echo ""
echo "TO VIEW BOOT PROGRESS:"
echo ""
echo " $ gcutil ssh --zone $ZONE --project $projectid $instancename tail -f /var/log/startupscript.log"
echo ""

externalip="$(
  gcutil getinstance $instancename \
    --zone $ZONE \
    --project $projectid \
    | grep 'external-ip' \
    | sed -e 's/ //g' \
    | cut -d'|' -f3
)"
url="http://$externalip/"
echo ""
echo "TO CONNECT TO THE INSTANCE ONCE IT'S RUNNING:"
echo ""
echo "  $url"
echo ""
