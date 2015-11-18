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

from gceapi.tests.functional import test_base


class TestMachineTypes(test_base.GCETestCase):
    @property
    def machine_types(self):
        res = self.api.compute.machineTypes()
        self.assertIsNotNone(
            res,
            'Null machineTypes object, api is not built properly')
        return res

    def _get_machine_type(self, name):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('Get machine type: project_id={} zone={} name={}'.format(
            project_id, zone, name))
        request = self.machine_types.get(project=project_id,
                                         zone=zone,
                                         machineType=name)
        result = request.execute()
        self.trace('Machine type: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='MachineType')
        return result

    def _list_machine_types(self, filter=None):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('List machine types: project_id={} zone={} filter={}'.
                   format(project_id, zone, filter))
        request = self.machine_types.list(project=project_id,
                                          zone=zone,
                                          filter=filter)
        result = request.execute()
        self.trace('Machine types: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='MachineTypeList')
        return result

    def _aggregated_list_machine_types(self, filter=None):
        project_id = self.cfg.project_id
        self.trace('Aggregated list machine types: project_id={} filter={}'.
                   format(project_id, filter))
        request = self.machine_types.aggregatedList(project=project_id,
                                                    filter=filter)
        result = request.execute()
        self.trace('Aggregated machine types: {}'.format(result))
        self.api.validate_schema(value=result,
                                 schema_name='MachineTypeAggregatedList')
        return result

    def _get_expected_machine_type(self, options):
        mt = copy.deepcopy(options)
        mt.setdefault('kind', 'compute#machineType')
        mt.setdefault('id', '[0-9]+')
        # TODO(alexey-mr): not supported by OS GCE
        # mt.setdefault('creationTimestamp', '.*')
        mt.setdefault('description', '.*')
        mt.setdefault('guestCpus', '[0-9]+')
        mt.setdefault('memoryMb', '[0-9]+')
        # not returned by Google by default
        # mt.setdefault('imageSpaceGb', '[0-9]+')
        # mt.setdefault('scratchDisks', {})
        mt.setdefault('maximumPersistentDisks', '[0-9]+')
        mt.setdefault('maximumPersistentDisksSizeGb', '[0-9]+')
        zone = mt.get('zone', self.cfg.zone)
        # TODO(alexey-mr): GCE returns names but OS GCE return full url
        mt['zone'] = '.*{}'.format(zone)
        self_link = self.api.get_zone_url(
            resource='machineTypes/{}'.format(mt['name']),
            zone=zone)
        mt.setdefault('selfLink', self_link)
        return mt

    def test_get_machine_type(self):
        name = self.cfg.machine_type
        result = self._get_machine_type(name)
        expected = self._get_expected_machine_type(options={'name': name})
        self.assertObject(expected, result)

    def test_list_machine_types(self):
        name = self.cfg.machine_type
        result = self._list_machine_types()
        result = self.assertFind(name, result)
        expected = self._get_expected_machine_type(options={'name': name})
        self.assertObject(expected, result)

    def test_aggregated_list_machine_types(self):
        result = self._aggregated_list_machine_types()
        self.assertIn('items', result)
        items = result['items']
        if len(items) == 0:
            self.fail('Empty aggregated machine types list')
        name = self.cfg.machine_type
        for zone, zone_list in items.items():
            result = self.assertFind(name, zone_list, key='machineTypes')
            options = {
                'name': name,
                'zone': zone.split('/')[-1]
            }
            expected = self._get_expected_machine_type(options)
            self.assertObject(expected, result)
