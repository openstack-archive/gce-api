# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from gceapi.api import zones
from gceapi.tests.unit.api import common
from gceapi.tests.unit.api import fake_request


REGION = fake_request.REGION
EXPECTED_ZONES = [{
    "id": "3924463100986466035",
    "kind": "compute#zone",
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
                "/zones/nova",
    "name": "nova",
    "status": "UP",
    "region": REGION,
}]


class ZonesControllerTest(common.GCEControllerTest):
    """
    Test of the GCE API /zones appliication.
    """

    def setUp(self):
        """Run before each test."""
        super(ZonesControllerTest, self).setUp()
        self.controller = zones.Controller()

    def test_get_zone_by_invalid_name(self):
        response = self.request_gce('/fake_project/zones/fakezone')
        self.assertEqual(404, response.status_int)

    def test_get_zone(self):
        response = self.request_gce('/fake_project/zones/nova')
        expected = EXPECTED_ZONES[0]

        self.assertEqual(response.json_body, expected)

    def test_get_zone_list_filtered(self):
        response = self.request_gce('/fake_project/zones?filter=name+eq+nova')
        expected = {
            "kind": "compute#zoneList",
            "id": "projects/fake_project/zones",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/zones",
            "items": [EXPECTED_ZONES[0]]
        }

        self.assertEqual(response.json_body, expected)

    def test_get_zone_list(self):
        response = self.request_gce('/fake_project/zones')
        expected = {
            "kind": "compute#zoneList",
            "id": "projects/fake_project/zones",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/zones",
            "items": EXPECTED_ZONES
        }

        self.assertEqual(response.json_body, expected)
