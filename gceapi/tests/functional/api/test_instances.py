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

import copy

from gceapi.tests.functional.api import test_addresses
from gceapi.tests.functional.api import test_disks


class TestInstancesBase(test_disks.TestDiskBase):
    @property
    def instances(self):
        res = self.api.compute.instances()
        self.assertIsNotNone(
            res,
            'Null instances object, api is not built properly')
        return res

    def _create_instance(self, options):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('Create instance with options {}'.format(options))
        request = self.instances.insert(
            project=project_id,
            zone=zone,
            body=options)
        self._add_cleanup(self._delete_instance, options['name'])
        self._execute_async_request(request, project_id, zone=zone)

    def _delete_instance(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('Delete instance: project_id={} zone={} instance {}'.
                   format(project_id, zone, name))
        request = self.instances.delete(
            project=project_id,
            zone=zone,
            instance=name)
        self._execute_async_request(request, project_id, zone=zone)
        self._remove_cleanup(self._delete_instance, name)

    def _list_instances(self, filter=None):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('List instances: project_id={} zone={}'.
                   format(project_id, zone))
        request = self.instances.list(
            project=project_id,
            zone=zone,
            filter=filter)
        self.trace_request(request)
        result = request.execute()
        self.trace('Instances: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='InstanceList')
        return result

    def _get_instance(self, name):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('Get instance: project_id={} zone={} instance={}'.
                   format(project_id, zone, name))
        request = self.instances.get(
            project=project_id,
            zone=zone,
            instance=name)
        result = request.execute()
        self.trace('Instance: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Instance')
        return result

    def _get_expected_attached_disk(self, options, instance_name):
        disk = copy.deepcopy(options)
        source = disk.get('source', 'disks/{}'.format(instance_name))
        disk['source'] = self.api.get_zone_url(source)
        disk.setdefault('kind', u'compute#attachedDisk')
        disk.setdefault('mode', u'READ_WRITE')
        # TODO(alexey-mr): OS GCE return vda
        # if disk.setdefault('type', u'PERSISTENT') == u'PERSISTENT':
        #     disk.setdefault('deviceName', 'persistent-disk-[0-9]+')
        is_boot = disk['boot'] = disk.get('boot', False)
        disk.setdefault('index', 0 if is_boot else '[0-9]+')
        # in case if autoDelete was set to 'False' during creation
        # gce does not return the field at all, so remove filed from check
        if not disk.get('autoDelete', False):
            disk.pop('autoDelete', None)
        # TODO(alexey-mr): OS gce api doesn't return interface
        # disk.setdefault('interface', u'SCSI')
        # remove input only parameters
        disk.pop('initializeParams', None)
        return disk

    @staticmethod
    def _get_expected_access_config(options):
        ac = copy.deepcopy(options)
        ac.setdefault('kind', u'compute#accessConfig')
        ac.setdefault('type', u'ONE_TO_ONE_NAT')
        return ac

    def _get_expected_nic(self, options):
        nic = copy.deepcopy(options)
        nic['network'] = self.api.get_project_url(nic['network'])
        nic.setdefault('networkIP', test_addresses.IPV4_PATTERN)
        # TODO(alexey-mr): OS GCE returns network name aka 'default'
        # nic.setdefault('name', 'nic[0-9]+')
        access_configs = nic.get('accessConfigs')
        if access_configs:
            acs = []
            for ac in access_configs:
                acs.append(self._get_expected_access_config(ac))
            nic['accessConfigs'] = acs
        return nic

    def _get_expected_instance(self, options):
        instance = copy.deepcopy(options)
        name = instance['name']
        # expected that machine_type here is in form of ralative zone url
        # aka 'zones/zone/machineTypes/machine_type or full absolute url
        machine_type_url = self.api.get_project_url(instance['machineType'])
        instance['machineType'] = machine_type_url
        attached_disks = list()
        for disk in instance['disks']:
            attached_disks.append(self._get_expected_attached_disk(disk, name))
        instance['disks'] = attached_disks
        network_interfaces = list()
        for nic in instance['networkInterfaces']:
            network_interfaces.append(self._get_expected_nic(nic))
        instance['networkInterfaces'] = network_interfaces
        instance.setdefault('kind', u'compute#instance')
        instance.setdefault('status', u'RUNNING')
        self_link = 'instances/{}'.format(name)
        instance.setdefault('selfLink', self.api.get_zone_url(self_link))
        instance.setdefault('zone', self.api.get_zone_url())
        # TODO(alexey-mr): OS gce doesn't return canIpForward => don't check
        instance.pop('canIpForward', None)
        # TODO(alexey-mr): OS gce api doesn't return scheduling
        # instance.setdefault(
        #     'scheduling',
        #     {
        #         'automaticRestart': True,
        #         'preemptible': False,
        #         'onHostMaintenance': u'MIGRATE'
        #     })
        return instance

    def _ensure_instance_created(self, options):
        expected_instance = self._get_expected_instance(options)
        instance = self._get_instance(options['name'])
        self.assertObject(expected_instance, instance)
        return instance

    def _get_create_instance_from_image_options(self, name):
        cfg = self.cfg
        machine_type = 'zones/{}/machineTypes/{}'.format(cfg.zone,
                                                         cfg.machine_type)
        image = 'projects/{}'.format(cfg.image)
        options = {
            'name': name,
            'machineType': machine_type,
            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': image
                    }
                }
            ],
            'networkInterfaces': [
                {
                    'network': 'global/networks/default',
                }
            ],
        }
        return options

    def _get_create_instance_from_disks_options(self, name, disks):
        cfg = self.cfg
        machine_type = 'zones/{}/machineTypes/{}'.format(cfg.zone,
                                                         cfg.machine_type)
        options = {
            'name': name,
            'machineType': machine_type,
            'disks': disks,
            'networkInterfaces': [
                {
                    'network': 'global/networks/default',
                }
            ],
        }
        return options


class TestInstances(TestInstancesBase):
    def test_create_delete_instance_from_image(self):
        name = self._rand_name('testinstance')
        options = self._get_create_instance_from_image_options(name)
        self._create_instance(options)
        self._ensure_instance_created(options)
        self._delete_instance(name)

    def test_list_instances(self):
        name = self._rand_name('testinstance')
        options = self._get_create_instance_from_image_options(name)
        self._create_instance(options)
        instance = self._ensure_instance_created(options)
        result = self._list_instances()
        result = self.assertFind(name, result)
        self.assertObject(instance, result)
        self._delete_instance(name)

    def test_list_instances_by_filter_name(self):
        names = [self._rand_name('testinstance') for _ in range(0, 3)]
        # prepare resources
        instances = dict()
        for name in names:
            options = self._get_create_instance_from_image_options(name)
            self._create_instance(options)
            instances[name] = self._ensure_instance_created(options)
        # do list by filter test
        for name in names:
            result = self._list_instances(filter='name eq {}'.format(name))
            self.assertEqual(1, len(result['items']))
            self.assertObject(instances[name], result['items'][0])
        # delete resources
        for name in names:
            self._delete_instance(name)

    def _create_boot_disk(self):
        image_name, image_project = self._parse_image_url(self.cfg.image)
        image = self._get_image(image_name, image_project)
        boot_disk = self._create_disk_from_image(image)
        opts = {
            'autoDelete': False,
            'boot': True,
            'source': boot_disk['selfLink']
        }
        return boot_disk, opts

    def _create_data_disk(self):
        name = self._rand_name('testdisk')
        options = {
            'name': name
        }
        self._create_disk(options)
        data_disk = self._ensure_disk_created(options)
        opts = {
            'autoDelete': False,
            'boot': False,
            'source': data_disk['selfLink']
        }
        return data_disk, opts

    def test_create_instance_from_disks(self):
        # TODO(alexey-mr): OS GCE does not support image creation from disk'
        if not self.full_compatibility:
            self.skipTest('OS GCE does not support image creation from disk')
            return
        name = self._rand_name('testinstance')
        boot_disk, boot_disk_opts = self._create_boot_disk()
        data_disk, data_disk_opts = self._create_data_disk()
        options = self._get_create_instance_from_disks_options(
            name,
            [boot_disk_opts, data_disk_opts]
        )
        self._create_instance(options)
        self._ensure_instance_created(options)
        self._delete_instance(name)
        self._delete_disk(boot_disk['name'])
        self._delete_disk(data_disk['name'])
