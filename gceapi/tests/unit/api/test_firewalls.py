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

import gceapi.context
from gceapi.tests.unit.api import common


DEFAULT_FIREWALL = {
    "kind": "compute#firewall",
    "name": "default",
    "creationTimestamp": "",
    "sourceRanges": [
        "0.0.0.0/0",
    ],
    "allowed": [],
    "id": "1000226411104458008",
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/default"),
    "description": "[+]default",
}
FAKE_FIREWALL_1 = {
    "kind": "compute#firewall",
    "name": "fake-firewall-1",
    "creationTimestamp": "2013-12-25T09:01:00.396957Z",
    "sourceRanges": [
        "55.0.0.0/24",
        "44.0.0.0/24",
    ],
    "allowed": [
        {
            "IPProtocol": "udp",
            "ports": [
                "223-322",
            ],
        },
        {
            "IPProtocol": "icmp",
        },
        {
            "IPProtocol": "tcp",
            "ports": [
                "1234",
            ],
        },
    ],
    "id": "5486539087303205175",
    "network": ("http://localhost/compute/v1beta15/projects"
                "/fake_project/global/networks/private"),
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/fake-firewall-1"),
    "description": "simple firewall",
}
FAKE_FIREWALL_2 = {
    "kind": "compute#firewall",
    "name": "fake-firewall-2",
    "creationTimestamp": "",
    "sourceRanges": [
        "0.0.0.0/0",
    ],
    "allowed": [],
    "id": "5486539087303205174",
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/fake-firewall-2"),
    "description": "openstack sg w/o rules",
}
FAKE_FIREWALL_3 = {
    "kind": "compute#firewall",
    "name": "fake-firewall-3",
    "creationTimestamp": "2013-12-25T09:02:00.396957Z",
    "sourceRanges": [
        "77.0.0.0/24",
        "78.0.0.0/24",
    ],
    "allowed": [
        {
            "IPProtocol": "tcp",
            "ports": [
                "1000-2000",
            ],
        },
    ],
    "id": "5486539087303205173",
    "network": ("http://localhost/compute/v1beta15/projects/"
                "fake_project/global/networks/private"),
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/fake-firewall-3"),
    "description": "[+]openstack sg with cidr & secgroup rules",
}
FAKE_FIREWALL_4 = {
    "kind": "compute#firewall",
    "name": "fake-firewall-4",
    "creationTimestamp": "",
    "sourceRanges": [],
    "allowed": [],
    "id": "5486539087303205172",
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/fake-firewall-4"),
    "description": "[*]openstack sg too complex to translate into gce rules",
}
FAKE_FIREWALL_5 = {
    "kind": "compute#firewall",
    "name": "fake-firewall-5",
    "creationTimestamp": "",
    "sourceRanges": [],
    "allowed": [],
    "id": "5486539087303205171",
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/fake-firewall-5"),
    "description": "[*][+]openstack sg with combined & too complex rules",
}
FAKE_FIREWALL_6 = {
    "kind": "compute#firewall",
    "name": "fake-firewall-6",
    "creationTimestamp": "",
    "sourceRanges": [],
    "allowed": [],
    "id": "5486539087303205170",
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/fake-firewall-6"),
    "description": "[*]openstack sg with too complex icmp rule",
}
NEW_FIREWALL = {
    "kind": "compute#firewall",
    "name": "new-firewall",
    "creationTimestamp": "2013-12-25T09:03:00.396957Z",
    "sourceRanges": [
        "42.0.0.0/24",
        "41.0.0.0/24",
    ],
    "allowed": [
        {
            "IPProtocol": "udp",
            "ports": [
                "5000-6000", "6666",
            ],
        },
        {
            "IPProtocol": "icmp",
        },
        {
            "IPProtocol": "tcp",
            "ports": [
                "80", "8080",
            ],
        },
    ],
    "id": "8518771050733866051",
    "network": ("http://localhost/compute/v1beta15/projects"
                "/fake_project/global/networks/private"),
    "selfLink": ("http://localhost/compute/v1beta15/projects"
                 "/fake_project/global/firewalls/new-firewall"),
    "description": "new fake firewall",
}


class FirewallsControllerTest(common.GCEControllerTest):

    def setUp(self):
        super(FirewallsControllerTest, self).setUp()

    def test_list_firewalls_filtered(self):
        response = self.request_gce("/fake_project/global/firewalls"
                                    "?filter=name+eq+fake-firewall-5")
        self.assertEqual(200, response.status_int)
        response_body = copy.deepcopy(response.json_body)
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#firewallList",
            "id": "projects/fake_project/global/firewalls",
            "selfLink": ("http://localhost/compute/v1beta15/projects/"
                         "fake_project/global/firewalls")
        }
        response_firewalls = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertDictInListBySelfLink(FAKE_FIREWALL_5, response_firewalls)

    def test_list_firewalls(self):
        response = self.request_gce("/fake_project/global/firewalls")
        self.assertEqual(200, response.status_int)
        response_body = copy.deepcopy(response.json_body)
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#firewallList",
            "id": "projects/fake_project/global/firewalls",
            "selfLink": ("http://localhost/compute/v1beta15/projects/"
                         "fake_project/global/firewalls")
        }
        response_firewalls = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertDictInListBySelfLink(DEFAULT_FIREWALL, response_firewalls)
        self.assertDictInListBySelfLink(FAKE_FIREWALL_1, response_firewalls)
        self.assertDictInListBySelfLink(FAKE_FIREWALL_2, response_firewalls)
        self.assertDictInListBySelfLink(FAKE_FIREWALL_3, response_firewalls)
        self.assertDictInListBySelfLink(FAKE_FIREWALL_4, response_firewalls)
        self.assertDictInListBySelfLink(FAKE_FIREWALL_5, response_firewalls)
        self.assertDictInListBySelfLink(FAKE_FIREWALL_6, response_firewalls)

    def test_get_firewall(self):
        response = self.request_gce(
                "/fake_project/global/firewalls/fake-firewall-1")
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(FAKE_FIREWALL_1, response.json_body)

    def test_create_firewall(self):
        self.add_to_instance_was_called = False

        def add_to_instance(dummy, context, instance, sg_id):
            self.assertIsInstance(context, gceapi.context.RequestContext)
            self.assertEqual("6472359b-d46b-4629-83a9-d2ec8d99468c",
                             instance["uuid"])
            self.assertEqual("5707a6f0-799d-4739-8740-3efc73f122aa", sg_id)
            self.add_to_instance_was_called = True

        request_body = {
            "network": ("http://localhost/compute/v1beta15/projects"
                        "/fake_project/global/networks/private"),
            "rules": [],
            "description": "new fake firewall",
            "sourceRanges": ["41.0.0.0/24", "42.0.0.0/24"],
            "allowed": [
                {"IPProtocol": "icmp"},
                {"IPProtocol": "tcp", "ports": ["80", "8080"]},
                {"IPProtocol": "udp", "ports": ["5000-6000", "6666"]},
            ],
            "name": "new-firewall",
        }
        response = self.request_gce("/fake_project/global/firewalls",
                                    method="POST",
                                    body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "insert",
            "targetId": "8518771050733866051",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/firewalls/new-firewall",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertDictEqual(expected, response.json_body)
        # TODO(apavlov): reanimate this
        #self.assertTrue(self.add_to_instance_was_called)
        #response = self.request_gce(
        #        "/fake_project/global/firewalls/new-firewall")
        #self.assertEqual(200, response.status_int)
        #self.assertDictEqual(NEW_FIREWALL, response.json_body)

    def test_delete_firewall(self):
        self.remove_from_instance_was_called = False

        def remove_from_instance(dummy, context, instance, sg_name):
            self.assertIsInstance(context, gceapi.context.RequestContext)
            self.assertEqual("6472359b-d46b-4629-83a9-d2ec8d99468c",
                             instance["uuid"])
            self.assertEqual("1aaa637b-87f4-4e27-bc86-ff63d30264b2", sg_name)
            self.remove_from_instance_was_called = True

        response = self.request_gce(
                "/fake_project/global/firewalls/to-delete-firewall",
                method="DELETE")
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "delete",
            "targetId": "7536069615864894672",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/firewalls/to-delete-firewall",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertDictEqual(expected, response.json_body)
        # TODO(apavlov): reanimate this
        #self.assertTrue(self.remove_from_instance_was_called)
        #response = self.request_gce(
        #        "/fake_project/global/firewalls/to-delete-firewall")
        #self.assertEqual(404, response.status_int)

    def test_delete_firewall_nonexistent(self):
        response = self.request_gce(
                "/fake_project/global/firewalls/fake-firewall",
                method="DELETE")
        self.assertEqual(404, response.status_int)
