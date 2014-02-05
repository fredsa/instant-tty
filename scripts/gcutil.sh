#!/bin/bash
#
set -ue

SCRIPTS_DIR=$( dirname $0 )
ROOT_DIR=$( dirname $SCRIPTS_DIR )

project=$( cat $ROOT_DIR/app.yaml | egrep '^application:' | sed 's/application: *\([0-9a-z][-0-9a-z]*[0-9a-z]\).*/\1/' )

echo
echo "Using project: $project"
echo

gcutil --project $project $*
