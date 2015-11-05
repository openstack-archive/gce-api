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


from gceapi.tests.functional import test_base


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


def _prepare_instance_insert_parameters(**kwargs):
    return test_base.insert_json_parameters(CREATE_INSTANCE_TEMPLATE, **kwargs)


class TestInstancesBase(test_base.GCETestCase):
    @property
    def instances(self):
        res = self.api.compute.instances()
        self.assertIsNotNone(
            res,
            'Null instances object, api is not built properly')
        return res

    def setUp(self):
        super(TestInstancesBase, self).setUp()
        self._instance_name = self.getUniqueString('testinst')

    def _create_instance(self):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        kw = {
            'zone': zone,
            'instance': self._instance_name,
            'machine_type': cfg.machine_type,
            'image': cfg.image,
            'network': 'default',
        }
        config = _prepare_instance_insert_parameters(**kw)
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
        self.trace('Delete instance: project_id={} zone={} instance {}'.
                   format(project_id, zone, instance))
        request = self.instances.delete(
            project=project_id,
            zone=zone,
            instance=instance)
        result = self._execute_async_request(request, project_id, zone=zone)
        self.api.validate_schema(value=result, schema_name='Operation')
        return result

    def _list_instances(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('List instances: project_id={} zone={}'.
                   format(project_id, zone))
        request = self.instances.list(project=project_id, zone=zone)
        self._trace_request(request)
        result = request.execute()
        self.trace('Instances: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='InstanceList')
        self.assertFind(self._instance_name, result)
        return result

    def _get_instance(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        instance = self._instance_name
        self.trace('Get instance: project_id={} zone={} instance={}'.
                   format(project_id, zone, instance))
        request = self.instances.get(
            project=project_id,
            zone=zone,
            instance=instance)
        result = request.execute()
        self.trace('Instance: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Instance')
        return result


class TestInstancesCRUD(TestInstancesBase):
    def _create(self):
        self._create_instance()

    def _read(self):
        self._get_instance()
        self._list_instances()

    def _update(self):
        # TODO(alexey-mr): to impl simple update cases
        pass

    def _delete(self):
        self._delete_instance()

    def test_crud(self):
        self._create()
        self._read()
        self._update()
        self._delete()
