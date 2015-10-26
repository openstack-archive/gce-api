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
    "description": "Testing instance",
    "machineType": "zones/${zone}/machineTypes/${machine_type}",
    "disks": [
        {
            "boot": True,
            "autoDelete": True,
            "initializeParams": {
                "sourceImage": "projects/${image}",
            }
        }
    ],
    "networkInterfaces": [
        {
            "network": "global/networks/${network}",
        }
    ],
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
CREATE_NETWORK_TEMPLATE = {
    "name": "${name}",
    "IPv4Range": "10.240.0.0/16",
    "description": "testing network ${name}",
    "gatewayIPv4": "10.240.0.1"
}


def _insert_json_parameters(obj, **kwargs):
    s = dumps(obj)
    t = Template(s)
    s = t.substitute(**kwargs)
    return loads(s)


def _prepare_instace_insert_parameters(**kwargs):
    return _insert_json_parameters(CREATE_INSTANCE_TEMPLATE, **kwargs)


def _prepare_network_create_parameters(**kwargs):
    return _insert_json_parameters(CREATE_NETWORK_TEMPLATE, **kwargs)


class TestIntancesBase(test_base.GCETestCase):
    @property
    def instances(self):
        res = self.api.compute.instances()
        self.assertIsNotNone(
            res,
            'Null instances object, api is not built properly')
        return res

    @property
    def networks(self):
        res = self.api.compute.networks()
        self.assertIsNotNone(
            res,
            'Null networks object, api is not built properly')
        return res

    def setUp(self):
        super(TestIntancesBase, self).setUp()
        self._instance_name = self.getUniqueString('testinst')
        self._network_name = self.getUniqueString('testnet')

    def _create_network(self):
        cfg = self.cfg
        project_id = cfg.project_id
        network = self._network_name
        kw = {
            'name': network,
        }
        config = _prepare_network_create_parameters(**kw)
        self.trace('Crete network with options {}'.format(config))
        request = self.networks.insert(
            project=project_id,
            body=config)
        result = self._execute_async_request(request, project_id)
        self.api.validate_schema(value=result, schema_name='Operation')
        return result

    def _delete_network(self):
        cfg = self.cfg
        project_id = cfg.project_id
        network = self._network_name
        self.trace(
            'Delete network: project_id={} network={}'.
                format(project_id, network))
        request = self.networks.delete(
            project=project_id,
            network=network)
        result = self._execute_async_request(request, project_id)
        self.api.validate_schema(value=result, schema_name='Operation')
        return result

    def _create_instance(self):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        kw = {
            'zone': zone,
            'instance': self._instance_name,
            'machine_type': cfg.machine_type,
            'image': cfg.image,
            'network': self._network_name,
        }
        config = _prepare_instace_insert_parameters(**kw)
        self.trace('Crete instance with options {}'.format(config))
        request = self.instances.insert(
            project=project_id,
            zone=zone,
            body=config)
        result = self._execute_async_request(request, project_id, zone=zone)
        self.api.validate_schema(value=result, schema_name='Operation')
        return result

    def _delete_instance(self):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        instance = self._instance_name
        self.trace(
            'Delete instance: project_id={} zone={} instance {}'.
                format(project_id, zone, instance))
        request = self.instances.delete(
            project=project_id,
            zone=zone,
            instance=instance)
        result = self._execute_async_request(request, project_id, zone=zone)
        self.api.validate_schema(value=result, schema_name='Operation')
        return result

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
        self.assertFind(self._instance_name, result)
        return result

    def _get(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        instance = self._instance_name
        self.trace(
            'Get instance: project_id={} zone={} instance={}'.
                format(project_id, zone, instance))
        request = self.instances.get(
            project=project_id,
            zone=zone,
            instance=instance)
        result = request.execute()
        self.trace('Instance: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Instance')
        return result


class TestIntancesCRUD(TestIntancesBase):
    def _create(self):
        self._create_network()
        self._create_instance()

    def _read(self):
        self._get()
        self._list()

    def _update(self):
        #TODO(to impl simple update cases)
        pass

    def _delete(self):
        self._delete_instance()
        self._delete_network()

    def test_crud(self):
        self._create()
        self._read()
        self._update()
        self._delete()
