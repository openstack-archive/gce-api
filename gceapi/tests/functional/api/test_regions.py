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


class TestRegions(test_base.GCETestCase):
    """
    Test perform two action:
        - list of available regions
        - describe a particular region (that is in config)
    Test expects project_id and testing region are to be set in test config.
    """

    @property
    def regions(self):
        res = self.api.compute.regions()
        self.assertIsNotNone(res,
                             'Null regions object, api is not built properly')
        return res

    def test_describe(self):
        project_id = self.cfg.project_id
        region = self.cfg.region
        self.trace('Describe region: project_id={} region={}'.format(
            project_id, region))
        result = self.regions.get(project=project_id, region=region).execute()
        self.trace('Region: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Region')

    def test_list(self):
        project_id = self.cfg.project_id
        self.trace('List regions: project_id={}'.format(project_id))
        result = self.regions.list(project=project_id).execute()
        self.trace('Regions: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='RegionList')
        self.assertFind(self.cfg.region, result)
