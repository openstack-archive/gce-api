#!/bin/bash -x
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is executed inside post_test_hook function in devstack gate.

# Sleep some time until all services are starting
sleep 5

export GCEAPI_DIR=$(readlink -f .)
export TEST_CONFIG="functional_tests.conf"

# bug somewhere
unset OS_AUTH_TYPE

function die() {
  echo "ERROR in $1: $2"
  exit 1
}
export -f die
function warn() {
  echo "WARNING in $1: $2"
}
export -f warn

if [[ ! -f $GCEAPI_DIR/$TEST_CONFIG ]]; then

  openstack endpoint list --os-identity-api-version=3
  openstack service list --long
  if [[ "$?" -ne "0" ]]; then
    echo "Looks like credentials are absent."
    exit 1
  fi

  STACK_USER=$(whoami) $GCEAPI_DIR/devstack/create_config $TEST_CONFIG
  if [[ "$?" -ne "0" ]]; then
    echo "Config creation has failed."
    exit 1
  fi
fi


sudo pip install virtualenv
sudo rm -rf .venv
sudo virtualenv .venv --system-site-package
sudo chown -R $USER .venv
source .venv/bin/activate
pip install -r test-requirements.txt
pip install google-api-python-client
sudo OS_STDOUT_CAPTURE=-1 OS_STDERR_CAPTURE=-1 OS_TEST_TIMEOUT=500 OS_TEST_LOCK_PATH=${TMPDIR:-'/tmp'} \
  python -m subunit.run discover -t ./ ./gceapi/tests/functional/api | subunit-2to1 | tools/colorizer.py
RETVAL=$?
deactivate

# Here can be some commands for log archiving, etc...

openstack flavor list
openstack image list
openstack server list --all-projects
openstack volume list --all-projects
cinder snapshot-list --all-tenants

exit $RETVAL
