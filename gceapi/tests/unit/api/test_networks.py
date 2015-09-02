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

from gceapi.api import networks
from gceapi.tests.unit.api import common


EXPECTED_NETWORKS = [{
    "kind": "compute#network",
    "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/global/networks/private",
    "name": "private",
    "id": "1543653731328164645",
    "IPv4Range": "10.0.0.0/24",
    "gatewayIPv4": "10.0.0.1",
    "creationTimestamp": "2013-12-25T09:05:07.396957Z",
    "description": "main network",
}, {
    "kind": "compute#network",
    "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/global/networks/public",
    "name": "public",
    "id": "8340158205161619676",
    "IPv4Range": "172.24.4.224/28",
    "gatewayIPv4": "172.24.4.225",
    "creationTimestamp": "",
}]


class NetworksControllerTest(common.GCEControllerTest):

    def setUp(self):
        """Run before each test."""
        super(NetworksControllerTest, self).setUp()
        self.controller = networks.Controller()

    def test_get_network_by_invalid_name(self):
        response = self.request_gce(
            '/fake_project/global/networks/wrongNetworkName')
        self.assertEqual(404, response.status_int)

    def test_get_network(self):
        response = self.request_gce('/fake_project/global/networks/public')
        expected = EXPECTED_NETWORKS[1]

        self.assertEqual(response.json_body, expected)

    def test_get_networks_list_filtered(self):
        response = self.request_gce("/fake_project/global/networks"
                                    "?filter=name+eq+public")
        expected = {
                "kind": "compute#networkList",
                "id": "projects/fake_project/global/networks",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                            "/fake_project/global/networks",
                "items": [EXPECTED_NETWORKS[1]]
                }

        self.assertEqual(response.json_body, expected)

    def test_get_networks_list(self):
        response = self.request_gce('/fake_project/global/networks')
        expected = {
                "kind": "compute#networkList",
                "id": "projects/fake_project/global/networks",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                            "/fake_project/global/networks",
                "items": EXPECTED_NETWORKS
                }

        self.assertEqual(response.json_body, expected)

    def test_create_network(self):
        request_body = {
                        "IPv4Range": "10.100.0.0/24",
                        "kind": "compute#network",
                        "gatewayIPv4": "10.100.0.1",
                        "name": "mynet",
                        "description": ""
                        }
        response = self.request_gce('/fake_project/global/networks',
                                    method="POST",
                                    body=request_body)

        expected = {
                    "operationType": "insert",
                    "targetId": "7132179741530156151",
                    "targetLink": "http://localhost/compute/v1beta15/projects"
                                  "/fake_project/global/networks/mynet",
                    }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertEqual(response.json_body, expected)

    def test_delete_network(self):
        response = self.request_gce(
                '/fake_project/global/networks/public', method='DELETE')
        expected = {
            "operationType": "delete",
            "targetId": "8340158205161619676",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/networks/public",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertEqual(expected, response.json_body)
