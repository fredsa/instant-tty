#!/bin/bash
#
set -eu

SCRIPT_DIR=$( dirname $0 )
ROOT_DIR=$( dirname $SCRIPT_DIR )

if [ $# == 1 ]
then
  projectid="$1"
  shift
else
  projectid=$( cat $ROOT_DIR/app.yaml | egrep '^application:' | sed 's/application: *\([0-9a-z][-0-9a-z]*[0-9a-z]\).*/\1/' )
fi

ZONE=us-central1-a

echo
echo "LISTING INSTANCES:"
instances=$(
  gcutil listinstances \
    --project=$projectid \
    --format=names
)

if [ ! -z "$instances" ]
then
  echo ""
  echo "WILL DELETE THESE INSTANCES:"
  for instance in $instances
  do
    echo "- $instance"
  done
  echo ""
  echo -e "Hit [ENTER] to confirm: \c"
  read dummy

  for instance in $instances
  do
    echo
    echo "DELETING INSTANCE $instance:"
    gcutil deleteinstance \
      --project=$projectid \
      $instance --delete_boot_pd --force &
  done
fi


echo
echo "LISTING DISKS:"
disks=$(
  gcutil listdisks \
    --project=$projectid \
    --format=names
)

if [ ! -z "$disks" ]
then
  echo ""
  echo "WILL DELETE THESE DISKS:"
  for disk in $disks
  do
    echo "- $disk"
  done
  echo ""
  echo -e "Hit [ENTER] to confirm: \c"
  read dummy

  for disk in $disks
  do
    echo
    echo "DELETING INSTANCE $disk:"
    gcutil deletedisk \
      --project=$projectid \
      $disk --force &
  done
fi

echo ""
echo "LISTING OPERATIONS:"
gcutil listoperations \
  --project=$projectid \
  --filter="status ne DONE"
