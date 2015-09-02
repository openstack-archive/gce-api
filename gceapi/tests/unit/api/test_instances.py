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

from gceapi.tests.unit.api import common

EXPECTED_INSTANCES = [{
    "kind": "compute#instance",
    "id": "3991024138321713624",
    "creationTimestamp": "2013-08-14T13:45:32Z",
    "zone":
        "http://localhost/compute/v1beta15/projects/fake_project/zones/nova",
    "status": "RUNNING",
    "statusMessage": "ACTIVE",
    "name": "i1",
    "description": "i1 description",
    "machineType": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/machineTypes/m1-small",
    "networkInterfaces": [{
        "network": "http://localhost/compute/v1beta15/projects/fake_project"
            "/global/networks/private",
        "networkIP": "10.0.1.3",
        "name": "private",
        "accessConfigs": [{
            "kind": "compute#accessConfig",
            "type": "ONE_TO_ONE_NAT",
            "name": "ip for i1",
            "natIP": "192.168.138.196"
        }]
    }],
    "disks": [{
        "autoDelete": False,
        "kind": "compute#attachedDisk",
        "index": 0,
        "type": "PERSISTENT",
        "mode": "READ_WRITE",
        "source": "http://localhost/compute/v1beta15/projects/fake_project"
            "/zones/nova/disks/i1",
        "deviceName": "christmas-tree",
        "boot": True,
    }],
    "metadata": {
        "kind": "compute#metadata",
        "items": [],
    },
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/instances/i1"
}, {
    "kind": "compute#instance",
    "id": "3991024138321713621",
    "creationTimestamp": "2013-08-14T13:46:36Z",
    "zone": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova",
    "status": "STOPPED",
    "statusMessage": "SUSPENDED",
    "name": "i2",
    "description": "i2 description",
    "machineType": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/machineTypes/m1-large",
    "networkInterfaces": [{
        "network": "http://localhost/compute/v1beta15/projects/fake_project"
            "/global/networks/default",
        "networkIP": "10.100.0.3",
        "name": "default",
        "accessConfigs": []
    }],
    "disks": [],
    "metadata": {
        "kind": "compute#metadata",
        "items": [],
    },
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project"
        "/zones/nova/instances/i2"
}]


class InstancesTest(common.GCEControllerTest):

    def setUp(self):
        super(InstancesTest, self).setUp()

    def test_get_instance_by_invalid_name(self):
        response = self.request_gce('/fake_project/zones/nova/instances/fake')
        self.assertEqual(404, response.status_int)

    def test_get_instance_by_name(self):
        response = self.request_gce('/fake_project/zones/nova/instances/i1')

        self.assertEqual(200, response.status_int)
        self.assertDictEqual(response.json_body, EXPECTED_INSTANCES[0])

    def test_get_instance_list_filtered(self):
        response = self.request_gce("/fake_project/zones/nova/instances"
                                    "?filter=name+eq+i1")
        expected = {
                "kind": "compute#instanceList",
                "id": "projects/fake_project/zones/nova/instances",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/instances",
                }

        response_body = copy.deepcopy(response.json_body)
        instances = response_body.pop("items")
        self.assertDictEqual(response_body, expected)
        self.assertEqual(len(instances), 1)
        self.assertDictEqual(instances[0], EXPECTED_INSTANCES[0])

    def test_get_instance_list(self):
        response = self.request_gce('/fake_project/zones/nova/instances')
        expected = {
                "kind": "compute#instanceList",
                "id": "projects/fake_project/zones/nova/instances",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/zones/nova/instances",
                }

        response_body = copy.deepcopy(response.json_body)
        instances = response_body.pop("items")
        self.assertDictEqual(response_body, expected)
        self.assertDictEqual(instances[0], EXPECTED_INSTANCES[0])
        self.assertDictEqual(instances[1], EXPECTED_INSTANCES[1])

    def test_get_instance_aggregated_list_filtered(self):
        response = self.request_gce("/fake_project/aggregated/instances"
                                    "?filter=name+eq+i2")

        expected = {
            "kind": "compute#instanceAggregatedList",
            "id": "projects/fake_project/aggregated/instances",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/instances",
            "items": {
                "zones/nova": {},
            }
        }

        response_body = copy.deepcopy(response.json_body)
        instances = response_body["items"]["zones/nova"].pop("instances")
        self.assertDictEqual(response_body, expected)
        self.assertEqual(len(instances), 1)
        self.assertDictEqual(instances[0], EXPECTED_INSTANCES[1])

    def test_get_instance_aggregated_list(self):
        response = self.request_gce('/fake_project/aggregated/instances')

        expected = {
            "kind": "compute#instanceAggregatedList",
            "id": "projects/fake_project/aggregated/instances",
            "selfLink": "http://localhost/compute/v1beta15/projects"
                "/fake_project/aggregated/instances",
            "items": {
                "zones/nova": {},
            }
        }

        response_body = copy.deepcopy(response.json_body)
        instances = response_body["items"]["zones/nova"].pop("instances")
        self.assertDictEqual(response_body, expected)
        self.assertDictInListBySelfLink(EXPECTED_INSTANCES[0], instances)
        self.assertDictInListBySelfLink(EXPECTED_INSTANCES[1], instances)

    def test_delete_instance_with_invalid_name(self):
        response = self.request_gce("/fake_project/zones/nova"
            "/instances/fake-instance", method="DELETE")
        self.assertEqual(404, response.status_int)

    def test_delete_instance(self):
        response = self.request_gce(
                "/fake_project/zones/nova/instances/i2",
                method="DELETE")
        expected = {
            "targetId": "3991024138321713621",
            "operationType": "delete",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i2",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_reset_instance(self):
        response = self.request_gce(
                "/fake_project/zones/nova/instances/i1/reset",
                method="POST")
        expected = {
            "operationType": "reset",
            "targetId": "3991024138321713624",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i1",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_create_instance(self):
        request_body = {
            "name": "i3",
            "description": "inst01descr",
            "machineType": "http://localhost/compute/v1beta15/projects/"
                "fake_project/zones/nova/m1-small",
            "disks": [{
                "kind": "compute#attachedDisk",
                "boot": True,
                "type": "PERSISTENT",
                "mode": "READ_WRITE",
                "deviceName": "vda",
                "zone": "http://localhost/compute/v1beta15/projects/"
                    "fake_project/zones/nova",
                "source": "http://localhost/compute/v1beta15/projects/"
                    "fake_project/zones/nova/disks/fake-disk-1"
            }],
            "networkInterfaces": [{
                "kind": "compute#instanceNetworkInterface",
                "network": ("http://localhost/compute/v1beta15/projects"
                    "/admin/fake_project/global/private"),
            }],
        }
        response = self.request_gce("/fake_project/zones/nova/instances",
                                    method="POST",
                                    body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "insert",
            "targetId": "3991024138321713622",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i3",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertDictEqual(expected, response.json_body)

    def test_add_access_config(self):
        request_body = {
            "name": "ip for i2",
            "type": "ONE_TO_ONE_NAT",
            "natIP": "192.168.138.195"
        }
        response = self.request_gce("/fake_project/zones/nova"
            "/instances/i2/addAccessConfig?networkInterface=default",
            method="POST",
            body=request_body)
        expected = {
            "operationType": "addAccessConfig",
            "targetId": "3991024138321713621",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i2",
        }
        expected.update(common.COMMON_ZONE_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_delete_access_config(self):
        response = self.request_gce("/fake_project/zones/nova/"
            "instances/i1/deleteAccessConfig"
            "?accessConfig=ip for i1"
            "&networkInterface=private",
            method="POST")
        expected = {
            "operationType": "deleteAccessConfig",
            "targetId": "3991024138321713624",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i1",
        }
        expected.update(common.COMMON_ZONE_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_attach_disk(self):
        request_body = {
            "deviceName": "ghost",
            "source": "http://localhost/compute/v1beta15/projects/fake_project"
                "/zones/nova/disks/i1"
        }
        response = self.request_gce("/fake_project/zones/nova"
            "/instances/i2/attachDisk",
            method="POST",
            body=request_body)
        expected = {
            "operationType": "attachDisk",
            "targetId": "3991024138321713621",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i2",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_detach_disk(self):
        response = self.request_gce("/fake_project/zones/nova/"
            "instances/i1/detachDisk?deviceName=christmas-tree",
            method="POST")
        expected = {
            "operationType": "detachDisk",
            "targetId": "3991024138321713624",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/instances/i1",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)
