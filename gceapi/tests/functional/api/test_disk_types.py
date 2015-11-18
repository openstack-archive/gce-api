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


TYPES = [
    'local-ssd',
    'pd-ssd',
    'pd-standard'
]


class TestDiskTypes(test_base.GCETestCase):
    @property
    def disk_types(self):
        res = self.api.compute.diskTypes()
        self.assertIsNotNone(
            res,
            'Null diskTypes object, api is not built properly')
        return res

    def setUp(self):
        if not self.full_compatibility:
            self.skipTest('Not supported in Openstack GCE API')
            return
        super(TestDiskTypes, self).setUp()

    def _get_disk_type(self, name):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('Get disk-type: project_id={} zone={} name={}'.format(
            project_id, zone, name))
        request = self.disk_types.get(project=project_id,
                                      zone=zone,
                                      diskType=name)
        result = request.execute()
        self.trace('Disk type: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='DiskType')
        return result

    def _check_disk_type_prperties(self, name, disk_type, zone=None):
        self.assertEqual(name, disk_type['name'])
        self.assertEqual(self.api.get_zone_url(zone=zone), disk_type['zone'])
        self.assertIn('description', disk_type)
        self.assertIn('validDiskSize', disk_type)
        self.assertIn('defaultDiskSizeGb', disk_type)
        self.assertIn('kind', disk_type)
        self.assertIn('creationTimestamp', disk_type)

    def test_get_disk_type(self):
        for t in TYPES:
            result = self._get_disk_type(t)
            self._check_disk_type_prperties(t, result)

    def test_list_disk_types(self):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('List disk types: project_id={} zone={}'.format(project_id,
                                                                   zone))
        result = self.disk_types.list(project=project_id, zone=zone).execute()
        self.trace('Disk types list: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='DiskTypeList')
        for t in TYPES:
            dt = self.assertFind(t, result)
            self._check_disk_type_prperties(t, dt)

    def test_aggregated_list_disk_types(self):
        cfg = self.cfg
        project_id = cfg.project_id
        self.trace(
            'Aggregated list disk types: project_id={}'.format(project_id))
        result = self.disk_types.aggregatedList(project=project_id).execute()
        self.trace('Aggregated disk types list: {}'.format(result))
        self.api.validate_schema(
            value=result,
            schema_name='DiskTypeAggregatedList')
        self.assertIn('items', result)
        items = result['items']
        if len(items) == 0:
            self.fail('Empty aggregated disk types list')
        for zone_resources in items.items():
            for t in TYPES:
                dt = self.assertFind(t, zone_resources[1], 'diskTypes')
                self._check_disk_type_prperties(t, dt, zone=zone_resources[0])
