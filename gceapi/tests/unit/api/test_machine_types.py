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

import copy

from gceapi.api import machine_types
from gceapi.tests.unit.api import common


EXPECTED_FLAVORS = [{
        "kind": "compute#machineType",
        "id": "7739288395178120473",
        "description": "",
        "name": "m1-small",
        "guestCpus": 1,
        "memoryMb": 2048,
        "imageSpaceGb": 20,
        "maximumPersistentDisks": 0,
        "maximumPersistentDisksSizeGb": "0",
        "zone": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova",
        "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova/machineTypes/m1-small"
        },
        {
        "kind": "compute#machineType",
        "id": "6065497922195565467",
        "description": "",
        "name": "m1-large",
        'scratchDisks': [{"diskGb": 870L}],
        "guestCpus": 4,
        "memoryMb": 8192,
        "imageSpaceGb": 80,
        "maximumPersistentDisks": 0,
        "maximumPersistentDisksSizeGb": "0",
        "zone": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova",
        "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova/machineTypes/m1-large"
        }]


class MachineTypesTest(common.GCEControllerTest):
    def setUp(self):
        super(MachineTypesTest, self).setUp()
        self.controller = machine_types.Controller()

    def test_get_machine_type_by_invalid_name(self):
        response = self.request_gce(
            '/fake_project//zones/nova/machineTypes/wrongMachineType')
        self.assertEqual(404, response.status_int)

    def test_get_flavor_by_name(self):
        response = self.request_gce(
            '/fake_project/zones/nova/machineTypes/m1-small')
        expected = EXPECTED_FLAVORS[0]

        self.assertDictEqual(response.json_body, expected)

    def test_get_flavor_list_filtered(self):
        response = self.request_gce("/fake_project/zones/nova/machineTypes"
                                    "?filter=name+eq+m1-large")
        expected = {
                "kind": "compute#machineTypeList",
                "id": "projects/fake_project/zones/nova/machineTypes",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/machineTypes",
                "items": [EXPECTED_FLAVORS[1]]
                }

        self.assertEqual(response.json_body, expected)

    def test_get_flavor_list_paged(self):
        response = self.request_gce("/fake_project/zones/nova/machineTypes"
                                    "?maxResults=1")
        expected = {
                "kind": "compute#machineTypeList",
                "id": "projects/fake_project/zones/nova/machineTypes",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/machineTypes",
                "items": [EXPECTED_FLAVORS[1]],
                "nextPageToken": "1"
                }

        self.assertDictEqual(response.json_body, expected)

        response = self.request_gce("/fake_project/zones/nova/machineTypes"
                                    "?maxResults=1&pageToken=1")
        expected = {
                "kind": "compute#machineTypeList",
                "id": "projects/fake_project/zones/nova/machineTypes",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/machineTypes",
                "items": [EXPECTED_FLAVORS[0]]
                }

        self.assertDictEqual(response.json_body, expected)

    def test_get_flavor_list(self):
        response = self.request_gce('/fake_project/zones/nova/machineTypes')
        expected = {
                "kind": "compute#machineTypeList",
                "id": "projects/fake_project/zones/nova/machineTypes",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/machineTypes",
                "items": EXPECTED_FLAVORS
                }

        self.assertEqual(response.json_body, expected)

    def test_get_flavor_aggregated_list(self):
        response = self.request_gce('/fake_project/aggregated/machineTypes')

        expected_flavors2 = copy.deepcopy(EXPECTED_FLAVORS)
        for flavor in expected_flavors2:
            flavor["zone"] = flavor["zone"].replace("nova", "unavailable_zone")
            flavor["selfLink"] = flavor["selfLink"].replace(
                "nova", "unavailable_zone")
            # NOTE(apavlov) fix id due to changed selfLink
            # (gce_api calculate id from selfLink)
            hashed_link = hash(flavor["selfLink"])
            flavor["id"] = hashed_link if hashed_link >= 0 else -hashed_link
            flavor["id"] = str(flavor["id"])

        expected = {
            "kind": "compute#machineTypeAggregatedList",
            "id": "projects/fake_project/aggregated/machineTypes",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/machineTypes",
            "items": {
                "zones/nova": {
                    "machineTypes": EXPECTED_FLAVORS
                },
            }
        }

        self.assertEqual(response.json_body, expected)
