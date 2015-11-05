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

from gceapi.api import addresses

from gceapi.tests.unit.api import common
from gceapi.tests.unit.api import fake_request


REGION = fake_request.REGION
EXPECTED_ADDRESSES = [{
    "kind": "compute#address",
    "id": "1870839154859306350",
    "creationTimestamp": "",
    "status": "IN USE",
    "region": "http://localhost/compute/v1beta15/projects/"
              "fake_project/regions/%s" % REGION,
    "name": "address-172-24-4-227",
    "description": "",
    "address": "172.24.4.227",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/%s/"
                "addresses/address-172-24-4-227" % REGION,
    "users": ["http://localhost/compute/v1beta15/projects/"
              "fake_project/zones/nova/instances/i1"]
}]


class AddressesTest(common.GCEControllerTest):

    def setUp(self):
        super(AddressesTest, self).setUp()
        self.controller = addresses.Controller()

    def test_get_address_by_invalid_name(self):
        response = self.request_gce("/fake_project/regions/"
                                    "%s/addresses/fake" % REGION)
        self.assertEqual(404, response.status_int)

    def test_get_address_by_name(self):
        response = self.request_gce(
            "/fake_project/regions/%s/addresses/address-172-24-4-227" % REGION)

        self.assertEqual(200, response.status_int)
        self.assertEqual(response.json_body, EXPECTED_ADDRESSES[0])

    def test_get_address_list_filtered(self):
        response = self.request_gce("/fake_project/regions/%s/addresses"
                                    "?filter=name+eq+address-172-24-4-227" %
                                    REGION)
        expected = {
                "kind": "compute#addressList",
                "id": "projects/fake_project/regions/%s/addresses" % REGION,
                "selfLink": "http://localhost/compute/v1beta15/projects"
                            "/fake_project/regions/%s/addresses" % REGION,
                "items": [EXPECTED_ADDRESSES[0]]
                }

        self.assertEqual(response.json_body, expected)

    def test_get_address_list(self):
        response = self.request_gce("/fake_project/regions/%s"
                                    "/addresses" % REGION)
        expected = {
                "kind": "compute#addressList",
                "id": "projects/fake_project/regions/%s/addresses" % REGION,
                "selfLink": "http://localhost/compute/v1beta15/projects"
                            "/fake_project/regions/%s/addresses" % REGION,
                "items": EXPECTED_ADDRESSES
                }

        self.assertEqual(response.json_body, expected)

    def test_get_address_aggregated_list_filtered(self):
        response = self.request_gce("/fake_project/aggregated/addresses"
                                    "?filter=name+eq+address-172-24-4-227")

        expected = {
            "kind": "compute#addressAggregatedList",
            "id": "projects/fake_project/aggregated/addresses",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/addresses",
            "items": {
                "regions/%s" % REGION: {
                    "addresses": [EXPECTED_ADDRESSES[0]]
                },
            }
        }

        self.assertEqual(response.json_body, expected)

    def test_get_address_aggregated_list(self):
        response = self.request_gce("/fake_project/aggregated/addresses")

        expected = {
            "kind": "compute#addressAggregatedList",
            "id": "projects/fake_project/aggregated/addresses",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/addresses",
            "items": {
                "regions/%s" % REGION: {
                    "addresses": EXPECTED_ADDRESSES
                },
            }
        }

        self.assertEqual(response.json_body, expected)

    def test_delete_address_with_invalid_name(self):
        response = self.request_gce(
            "/fake_project/regions/%s/addresses/fake-address" % REGION,
            method="DELETE")
        self.assertEqual(404, response.status_int)

    def test_delete_address(self):
        response = self.request_gce(
            "/fake_project/regions/%s/addresses/address-172-24-4-227" % REGION,
            method="DELETE")
        expected = {
            "operationType": "delete",
            "targetId": "1870839154859306350",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/%s/"
                "addresses/address-172-24-4-227" % REGION,
        }
        expected.update(common.COMMON_REGION_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_create_address(self):
        request_body = {
            "name": "fake-address",
        }
        response = self.request_gce("/fake_project/regions/%s/"
                                    "addresses" % REGION,
                                    method="POST",
                                    body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "insert",
            "targetId": "8754519975833457287",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/regions/%s/addresses/fake-address" %
                          REGION,
        }
        expected.update(common.COMMON_REGION_FINISHED_OPERATION)
        self.assertDictEqual(expected, response.json_body)
