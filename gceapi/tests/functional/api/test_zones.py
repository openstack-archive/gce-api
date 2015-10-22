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


class TestZones(test_base.GCETestCase):
    """
    Test perform two actions: list of available zones and get info about
    a particular zone. Test expects project_id and zone are to be set in
    test config.
    """

    @property
    def zones(self):
        res = self.api.compute.zones()
        self.assertIsNotNone(res,
                             'Null regions object, api is not built properly')
        return res

    def test_get_zone(self):
        project_id = self.cfg.project_id
        zone = self.cfg.zone
        self.trace('Get zone: project_id={} zone={}'.format(project_id, zone))
        result = self.zones.get(project=project_id, zone=zone).execute()
        self.trace('Zone: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Zone')

    def test_list_zones(self):
        project_id = self.cfg.project_id
        self.trace('List zones: project_id={}'.format(project_id))
        result = self.zones.list(project=project_id).execute()
        self.trace('Zones: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='ZoneList')
        self.assertFind(self.cfg.zone, result)
