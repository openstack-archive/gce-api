#    Copyright 2013 Cloudscaling Group, Inc
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

from gceapi.api import addresses
from gceapi.tests.api import common

EXPECTED_ADDRESSES = [{
    "kind": "compute#address",
    "id": "2729532145628373701",
    "creationTimestamp": "",
    "status": "IN USE",
    "region": "http://localhost/compute/v1beta15/projects/"
        "fake_project/regions/nova",
    "name": "address-172-24-4-227",
    "description": "",
    "address": "172.24.4.227",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
        "fake_project/regions/nova/addresses/address-172-24-4-227",
    "users": ["http://localhost/compute/v1beta15/projects/"
        "fake_project/zones/nova/instances/i1"]
}]


class AddressesTest(common.GCEControllerTest):

    def setUp(self):
        super(AddressesTest, self).setUp()
        self.controller = addresses.Controller()

    def test_get_address_by_invalid_name(self):
        response = self.request_gce("/fake_project/regions/"
                                    "nova/addresses/fake")
        self.assertEqual(404, response.status_int)

    def test_get_address_by_name(self):
        response = self.request_gce("/fake_project/regions/"
                                    "nova/addresses/address-172-24-4-227")

        self.assertEqual(200, response.status_int)
        self.assertEqual(response.json_body, EXPECTED_ADDRESSES[0])

    def test_get_address_list_filtered(self):
        response = self.request_gce("/fake_project/regions/nova/addresses"
                                    "?filter=name+eq+address-172-24-4-227")
        expected = {
                "kind": "compute#addressList",
                "id": "projects/fake_project/regions/nova/addresses",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/regions/nova/addresses",
                "items": [EXPECTED_ADDRESSES[0]]
                }

        self.assertEqual(response.json_body, expected)

    def test_get_address_list(self):
        response = self.request_gce("/fake_project/regions/nova/addresses")
        expected = {
                "kind": "compute#addressList",
                "id": "projects/fake_project/regions/nova/addresses",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/regions/nova/addresses",
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
                "regions/nova": {
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
                "regions/nova": {
                    "addresses": EXPECTED_ADDRESSES
                },
            }
        }

        self.assertEqual(response.json_body, expected)

    def test_delete_address_with_invalid_name(self):
        response = self.request_gce("/fake_project/regions/nova"
            "/addresses/fake-address", method="DELETE")
        self.assertEqual(404, response.status_int)

    def test_delete_address(self):
        response = self.request_gce(
                "/fake_project/regions/nova/addresses/address-172-24-4-227",
                method="DELETE")
        expected = {
            "operationType": "delete",
            "targetId": "2729532145628373701",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/nova/addresses/address-172-24-4-227",
        }
        expected.update(common.COMMON_REGION_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_create_address(self):
        request_body = {
            "name": "fake-address",
        }
        response = self.request_gce("/fake_project/regions/nova/addresses",
                                    method="POST",
                                    body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "insert",
            "targetId": "5571612063911429008",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/regions/nova/addresses/fake-address",
        }
        expected.update(common.COMMON_REGION_FINISHED_OPERATION)
        self.assertDictEqual(expected, response.json_body)
