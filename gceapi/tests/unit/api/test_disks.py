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


EXPECTED_DISK_1 = {
    "status": "READY",
    "sourceSnapshot": "http://localhost/compute/v1beta15/projects/"
                      "fake_project/global/snapshots/fake-snapshot",
    "kind": "compute#disk",
    "name": "fake-disk-1",
    "sizeGb": '2',
    "sourceSnapshotId": "991cda9c-28bd-420f-8432-f5159def85d6",
    "zone": "http://localhost/compute/v1beta15/projects/"
            "fake_project/zones/nova",
    "creationTimestamp": "2013-08-14T12:35:22Z",
    "id": "9202387718698825408",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/zones/nova/disks/fake-disk-1",
    "description": "fake disk from snapshot",
}
EXPECTED_DISK_2 = {
    "status": "READY",
    "sizeGb": '1',
    "kind": "compute#disk",
    "name": "fake-disk-2",
    "zone": "http://localhost/compute/v1beta15/projects/"
            "fake_project/zones/nova",
    "creationTimestamp": "2013-08-14T12:19:35Z",
    "id": "9202387718698825405",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/zones/nova/disks/fake-disk-2",
    "description": "",
    "sourceImage": "http://localhost/compute/v1beta15/projects/fake_project"
                   "/global/images/fake-image-1",
    "sourceImageId": "5721131091780319465",
}
EXPECTED_DISK_3 = {
    "status": "READY",
    "sizeGb": '3',
    "kind": "compute#disk",
    "name": "fake-disk-3",
    "zone": "http://localhost/compute/v1beta15/projects/"
            "fake_project/zones/nova",
    "creationTimestamp": "2013-08-14T11:57:44Z",
    "id": "9202387718698825406",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/zones/nova/disks/fake-disk-3",
    "description": "full description of disk",
}
NEW_DISK = {
    "status": "READY",
    "sizeGb": '15',
    "kind": "compute#disk",
    "name": "new-disk",
    "zone": "http://localhost/compute/v1beta15/projects/"
            "fake_project/zones/nova",
    "creationTimestamp": "2013-08-14T15:00:22Z",
    "id": "5151144363316117590",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/zones/nova/disks/new-disk",
}
NEW_IMAGE_DISK = {
    "status": "READY",
    "kind": "compute#disk",
    "name": "new-image-disk",
    "sizeGb": '1',
    "sourceImage": "http://localhost/compute/v1beta15/projects/"
                   "fake_project/global/images/fake-image-2",
    "sourceImageId": "5721131091780319468",
    "zone": "http://localhost/compute/v1beta15/projects/"
            "fake_project/zones/nova",
    "creationTimestamp": "2013-08-14T15:56:00Z",
    "id": "3094468787955188924",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/zones/nova/disks/new-image-disk",
    "description": "disk created with image",
}
NEW_SN_DISK = {
    "status": "CREATING",
    "sourceSnapshot": "http://localhost/compute/v1beta15/projects/"
                      "fake_project/global/snapshots/fake-snapshot",
    "kind": "compute#disk",
    "name": "new-sn-disk",
    "sizeGb": '25',
    "sourceSnapshotId": "991cda9c-28bd-420f-8432-f5159def85d6",
    "zone": "http://localhost/compute/v1beta15/projects/"
            "fake_project/zones/nova",
    "creationTimestamp": "2013-08-14T16:43:59Z",
    "id": "5322910296130766655",
    "selfLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/zones/nova/disks/new-sn-disk",
    "description": "disk created from snapshot"
}


class DisksControllerTest(common.GCEControllerTest):
    def setUp(self):
        super(DisksControllerTest, self).setUp()

    def test_get_disk_list_filterd(self):
        response = self.request_gce("/fake_project/aggregated/disks"
                                    "?filter=name+eq+fake-disk-3")
        self.assertEqual(200, response.status_int)
        response_body = copy.deepcopy(response.json_body)
        self.assertIn("items", response_body)
        self.assertIn("zones/nova", response_body["items"])
        expected_common = {
            "kind": "compute#diskAggregatedList",
            "id": "projects/fake_project/aggregated/disks",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/aggregated/disks",
            "items": {
                "zones/nova": {},
            },
        }
        response_disks = response_body["items"]["zones/nova"].pop("disks")
        self.assertDictEqual(expected_common, response_body)
        self.assertDictInListBySelfLink(EXPECTED_DISK_3, response_disks)

    def test_get_disk_list(self):
        response = self.request_gce("/fake_project/aggregated/disks")
        self.assertEqual(200, response.status_int)
        response_body = copy.deepcopy(response.json_body)
        self.assertIn("items", response_body)
        self.assertIn("zones/nova", response_body["items"])
        expected_common = {
            "kind": "compute#diskAggregatedList",
            "id": "projects/fake_project/aggregated/disks",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/aggregated/disks",
            "items": {
                "zones/nova": {},
            },
        }
        response_disks = response_body["items"]["zones/nova"].pop("disks")
        self.assertDictEqual(expected_common, response_body)
        self.assertDictInListBySelfLink(EXPECTED_DISK_1, response_disks)
        self.assertDictInListBySelfLink(EXPECTED_DISK_2, response_disks)
        self.assertDictInListBySelfLink(EXPECTED_DISK_3, response_disks)

    def test_get_disk_by_name(self):
        response = self.request_gce(
                "/fake_project/zones/nova/disks/fake-disk-1")
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(EXPECTED_DISK_1, response.json_body)

    def test_get_disk_by_invalid_name(self):
        response = self.request_gce(
                "/fake_project/zones/nova/disks/fake-disk")
        self.assertEqual(404, response.status_int)

    def test_create_disk(self):
        request_body = {
            "name": "new-disk",
            "sizeGb": "15",
        }
        response = self.request_gce("/fake_project/zones/nova/disks",
                                    method="POST",
                                    body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "targetId": "5151144363316117590",
            "operationType": "insert",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/disks/new-disk",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertDictEqual(expected, response.json_body)
        response = self.request_gce(
                "/fake_project/zones/nova/disks/new-disk")
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(NEW_DISK, response.json_body)

    def test_create_disk_by_image(self):
        request_body = {
            "name": "new-image-disk",
            "description": "disk created with image"
        }
        response = self.request_gce(
                "/fake_project/zones/nova/disks?sourceImage=fake-image-2",
                method="POST",
                body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "insert",
            "targetId": "3094468787955188924",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/disks/new-image-disk",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertDictEqual(expected, response.json_body)
        response = self.request_gce(
                "/fake_project/zones/nova/disks/new-image-disk")
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(NEW_IMAGE_DISK, response.json_body)

    def test_create_disk_by_snapshot(self):
        request_body = {
            "name": "new-sn-disk",
            "sizeGb": "25",
            "sourceSnapshot": "http://localhost/compute/v1beta15/projects/"
                              "fake_project/global/snapshots/fake-snapshot",
            "description": "disk created from snapshot"
        }
        response = self.request_gce(
                "/fake_project/zones/nova/disks",
                method="POST",
                body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "insert",
            "targetId": "5322910296130766655",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/disks/new-sn-disk",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertDictEqual(expected, response.json_body)
        response = self.request_gce(
                "/fake_project/zones/nova/disks/new-sn-disk")
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(NEW_SN_DISK, response.json_body)

    def test_delete_disk(self):
        response = self.request_gce(
                "/fake_project/zones/nova/disks/disk-to-delete",
                method="DELETE")
        expected = {
            "operationType": "delete",
            "targetId": "7382604722864765133",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/disks/disk-to-delete",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_delete_disk_with_invalid_name(self):
        response = self.request_gce('/fake_project/zones/nova/disks/fake-disk',
                                    method="DELETE")
        self.assertEqual(404, response.status_int)
