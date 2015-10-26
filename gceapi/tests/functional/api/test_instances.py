# Copyright 2015 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from string import Template

from json import dumps
from json import loads

from gceapi.tests.functional import test_base


BASE_COMPUTE_URL = '{address}/compute/v1'
CREATE_INSTANCE_TEMPLATE = {
    "name": "${instance}",
    "zone": "projects/${project_id}/zones/${zone}",
    "machineType": "projects/${project_id}/zones/${zone}/"
                   "machineTypes/${machine_type}",
    "metadata": {
        "items": [
            {
                "key": "test_metadata_key",
                "value": "test_metadata_value"
            },
            {
                "key": "startup-script",
                "value": "echo Test startup script"
            }
        ]
    },
    "tags": {
        "items": [
            "test"
        ]
    },
    "disks": [
        {
            "type": "PERSISTENT",
            "boot": True,
            "mode": "READ_WRITE",
            "deviceName": "${disk_device_name}",
            "autoDelete": True,
            "initializeParams": {
                "sourceImage": "projects/${image}",
                "diskType": "projects/${project_id}/zones/${zone}"
                            "/diskTypes/${disk_type}",
                "diskSizeGb": "10"
            }
        }
    ],
    "canIpForward": False,
    "networkInterfaces": [
        {
            "network": "global/networks/${network}",
            "accessConfigs": [
                {
                    "name": "External NAT",
                    "type": "ONE_TO_ONE_NAT"
                }
            ]
        }
    ],
    "description": "Testing instance",
    "scheduling": {
        "preemptible": False,
        "onHostMaintenance": "MIGRATE",
        "automaticRestart": True
    },
    "serviceAccounts": [
        {
            "email": "default",
            "scopes": [
                "https://www.googleapis.com/auth/cloud.useraccounts.readonly",
                "https://www.googleapis.com/auth/devstorage.read_only",
                "https://www.googleapis.com/auth/logging.write",
                "https://www.googleapis.com/auth/monitoring.write"
            ]
        }
    ]
}


def _insert_json_parameters(obj, **kwargs):
    s = dumps(obj)
    t = Template(s)
    s = t.substitute(**kwargs)
    return loads(s)


def _prepare_instace_insert_parameters(**kwargs):
    return _insert_json_parameters(CREATE_INSTANCE_TEMPLATE, **kwargs)


class TestIntancesBase(test_base.GCETestCase):
    @property
    def instances(self):
        res = self.api.compute.instances()
        self.assertIsNotNone(
            res,
            'Null instances object, api is not built properly')
        return res

    def setUp(self):
        super(TestIntancesBase, self).setUp()
        self.instance_name = self.cfg.instance.format(self.getUniqueInteger())

    def _create(self):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        kw = {
            'base_url': BASE_COMPUTE_URL.format(address=self.api.base_url),
            'project_id': project_id,
            'zone': zone,
            'instance': self.instance_name,
            'machine_type': cfg.machine_type,
            'image': cfg.image,
            'disk_type': cfg.disk_type,
            'disk_device_name': 'disk_{}'.format(self.instance_name),
            'network': cfg.network,
        }
        config = _prepare_instace_insert_parameters(**kw)
        self.trace('Crete instance with options {}'.format(config))
        request = self.instances.insert(
            project=project_id,
            zone=zone,
            body=config)
        result = self._execute_async_request(project_id, zone, request)
        self.api.validate_schema(value=result, schema_name='Operation')

    def _list(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace(
            'List instances: project_id={} zone={}'.format(project_id, zone))
        request = self.instances.list(project=project_id, zone=zone)
        self._trace_request(request)
        result = request.execute()
        self.trace('Instances: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='InstanceList')
        self.assertFind(self.instance_name, result)
        return result

    def _get(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        instance = self.instance_name
        self.trace(
            'Get instance: project_id={} zone={}'.format(project_id, zone))
        request = self.instances.get(
            project=project_id,
            zone=zone,
            instance=instance)
        result = request.execute()
        self.trace('Instance: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Instance')
        return result

    def _read(self):
        self._get()
        self._list()

    def _update(self):
        #TODO(to impl simple update cases)
        pass

    def _delete(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        instance = self.instance_name
        self.trace(
            'Delete instance: project_id={} zone={}'.format(project_id, zone))
        request = self.instances.delete(
            project=project_id,
            zone=zone,
            instance=instance)
        result = self._execute_async_request(project_id, zone, request)
        self.api.validate_schema(value=result, schema_name='Operation')


class TestIntancesCRUD(TestIntancesBase):
    def test_crud(self):
        self._create()
        self._read()
        self._update()
        self._delete()
