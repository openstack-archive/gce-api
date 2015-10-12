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
from jsonschema import validate


class TestZones(test_base.GCETestCase):
    """
    Test perform two actions: list of available zones and get info about
    a particular zone. Test expects project_id and zone are to be set in
    test config.
    """

    def zones(self):
        return self.api.compute.zones()

    def test_list_zones(self):
        project_id = self.cfg.project_id
        self.trace('List zones: project_id={}'.format(project_id))
        result = self.zones().list(project=project_id).execute()
        self.trace('Zones: {}'.format(result))
        self._validate_zones(result)

    def test_get_zone(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('Get zone: project_id={} zone={}'.format(project_id, zone))
        result = self.zones().get(project=project_id, zone=zone).execute()
        self.trace('Zone: {}'.format(result))
        self._validate_zone(result)

    def _validate_zones(self, zones):
        self.assertIsNotNone(zones, 'Null zone list object')
        self.assertIs(True, len(zones) > 0, 'Empty zone list object')
        for z in zones['items']:
            self._validate_zone(z)

    def _validate_zone(self, zone):
        self.assertIsNotNone(zone, 'Null zone object')
        validate(zone, self.cfg.schema['schemas']['Zone'])
