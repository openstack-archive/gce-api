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

export TEST_CONFIG_DIR=$(readlink -f .)
export TEST_CONFIG="functional_tests.conf"

# save original creds(admin) for later usage
OLD_OS_PROJECT_NAME=$OS_PROJECT_NAME
OLD_OS_USERNAME=$OS_USERNAME
OLD_OS_PASSWORD=$OS_PASSWORD

# bug somewhere
unset OS_AUTH_TYPE

if [[ ! -f $TEST_CONFIG_DIR/$TEST_CONFIG ]]; then

  openstack endpoint list --os-identity-api-version=3
  openstack service list --long
  if [[ "$?" -ne "0" ]]; then
    echo "Looks like credentials are absent."
    exit 1
  fi

  # create separate user/project
  project_name="project-$(cat /dev/urandom | tr -cd 'a-f0-9' | head -c 8)"
  eval $(openstack project create -f shell -c id $project_name)
  project_id=$id
  [[ -n "$project_id" ]] || { echo "Can't create project"; exit 1; }
  user_name="user-$(cat /dev/urandom | tr -cd 'a-f0-9' | head -c 8)"
  password='password'
  eval $(openstack user create "$user_name" --project "$project_id" --password "$password" --email "$user_name@example.com" -f shell -c id)
  user_id=$id
  [[ -n "$user_id" ]] || { echo "Can't create user"; exit 1; }
  # add 'Member' role for swift access
  role_id=$(openstack role show  Member -c id -f value)
  openstack role add --project $project_id --user $user_id $role_id

  # prepare flavors
  flavor_name="n1.standard.1"
  if [[ -z "$(nova flavor-list | grep $flavor_name)" ]]; then
    nova flavor-create --is-public True $flavor_name 16 512 0 1
    [[ "$?" -eq 0 ]] || { echo "Failed to prepare flavor"; exit 1; }
  fi

  # create network
  if [[ -n $(openstack service list | grep neutron) ]]; then
    net_id=$(neutron net-create --tenant-id $project_id "private" | grep ' id ' | awk '{print $4}')
    [[ -n "$net_id" ]] || { echo "net-create failed"; exit 1; }
    subnet_id=$(neutron subnet-create --tenant-id $project_id --ip_version 4 --gateway 10.0.0.1 --name "private_subnet" $net_id 10.0.0.0/24 | grep ' id ' | awk '{print $4}')
    [[ -n "$subnet_id" ]] || { echo "subnet-create failed"; exit 1; }
    router_id=$(neutron router-create --tenant-id $project_id "private_router" | grep ' id ' | awk '{print $4}')
    [[ -n "$router_id" ]] || { echo "router-create failed"; exit 1; }
    neutron router-interface-add $router_id $subnet_id
    [[ "$?" -eq 0 ]] || { echo "router-interface-add failed"; exit 1; }
    public_net_id=$(neutron net-list | grep public | awk '{print $2}')
    [[ -n "$public_net_id" ]] || { echo "can't find public network"; exit 1; }
    neutron router-gateway-set $router_id $public_net_id
    [[ "$?" -eq 0 ]] || { echo "router-gateway-set failed"; exit 1; }
  fi

  #create image in raw format
  os_image_name="cirros-0.3.4-raw-image"
  if [[ -z "$(openstack image list | grep $os_image_name)" ]]; then
    image_name="cirros-0.3.4-x86_64-disk.img"
    cirros_image_url="http://download.cirros-cloud.net/0.3.4/$image_name"
    sudo rm -f /tmp/$image_name
    wget -nv -P /tmp $cirros_image_url
    [[ "$?" -eq 0 ]] || { echo "Failed to download image"; exit 1; }
    openstack image create --disk-format raw --container-format bare --public --file "/tmp/$image_name" $os_image_name
    [[ "$?" -eq 0 ]] || { echo "Failed to prepare image"; exit 1; }
  fi

  export OS_PROJECT_NAME=$project_name
  export OS_TENANT_NAME=$project_name
  export OS_USERNAME=$user_name
  export OS_PASSWORD=$password

  sudo bash -c "cat > $TEST_CONFIG_DIR/$TEST_CONFIG <<EOF
[gce]
# Generic options
build_timeout=${TIMEOUT:-180}
build_interval=1

# GCE API schema
schema=${GCE_SCHEMA:-'etc/gceapi/protocols/v1.json'}

# GCE auth options
cred_type=${GCE_CRED_TYPE:-'os_token'}
auth_url=${OS_AUTH_URL}
username=${OS_USERNAME}
password=${OS_PASSWORD}

# GCE services address
protocol=${GCE_API_PROTOCOL:-'http'}
host=${GCE_HOST:-'localhost'}
port=${GCE_PORT:-8787}

# GCE API URLs
discovery_url=${GCE_DISCOVERY_URL:-'/discovery/v1/apis/{api}/{apiVersion}/rest'}

# GCE resource IDs for testing
project_id=${OS_PROJECT_NAME}
zone=${ZONE:-'nova'}
region=${REGION:-'RegionOne'}
# convert flavor name: becase GCE dowsn't allows '.' and converts '-' into '.'
machine_type=${flavor_name//\./-}
image=${os_image_name}
EOF"
fi

sudo pip install -r test-requirements.txt
sudo pip install google-api-python-client
sudo OS_STDOUT_CAPTURE=-1 OS_STDERR_CAPTURE=-1 OS_TEST_TIMEOUT=500 OS_TEST_LOCK_PATH=${TMPDIR:-'/tmp'} \
  python -m subunit.run discover -t ./ ./gceapi/tests/functional | subunit-2to1 | tools/colorizer.py
RETVAL=$?

# Here can be some commands for log archiving, etc...

echo Enumerate resources to check what left after tests
for i in instances images disks snapshots
do
  echo "List of "$i
  gcloud compute $i list
  echo ""
done
export OS_PROJECT_NAME=$OLD_OS_PROJECT_NAME
export OS_TENANT_NAME=$OLD_OS_PROJECT_NAME
export OS_USERNAME=$OLD_OS_USERNAME
export OS_PASSWORD=$OLD_OS_PASSWORD
openstack flavor list
openstack image list
openstack server list --all-projects
openstack volume list --all-projects
cinder snapshot-list --all-tenants

exit $RETVAL
