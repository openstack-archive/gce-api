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

from gceapi.api import snapshots
from gceapi.tests.unit.api import common

EXPECTED_SNAPSHOTS = [{
    "kind": "compute#snapshot",
    "selfLink": "http://localhost/compute/v1beta15/projects/fake_project/"
        "global/snapshots/fake-snapshot",
    "id": "8386122516930476063",
    "creationTimestamp": "2013-08-14T12:32:28Z",
    "status": "READY",
    "diskSizeGb": "2",
    "sourceDisk": "http://localhost/compute/v1beta15/projects/"
        "fake_project/zones/nova/disks/fake-disk-3",
    "name": "fake-snapshot",
    "description": "full description of snapshot 1",
    "sourceDiskId": "9202387718698825406"
}]


class SnapshotsTest(common.GCEControllerTest):

    def setUp(self):
        super(SnapshotsTest, self).setUp()
        self.controller = snapshots.Controller()

    def test_get_snapshot_by_invalid_name(self):
        response = self.request_gce("/fake_project/global/snapshots/fake")
        self.assertEqual(404, response.status_int)

    def test_get_snapshot_by_name(self):
        response = self.request_gce("/fake_project/global/snapshots"
                                    "/fake-snapshot")

        self.assertEqual(200, response.status_int)
        self.assertDictEqual(response.json_body, EXPECTED_SNAPSHOTS[0])

    def test_get_snapshot_list_filtered(self):
        response = self.request_gce("/fake_project/global/snapshots"
                                    "?filter=name+eq+fake-snapshot")
        expected = {
                "kind": "compute#snapshotList",
                "id": "projects/fake_project/global/snapshots",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/global/snapshots",
                "items": [EXPECTED_SNAPSHOTS[0]]
                }

        self.assertEqual(response.json_body, expected)

    def test_get_snapshot_list(self):
        response = self.request_gce("/fake_project/global/snapshots")
        expected_common = {
                "kind": "compute#snapshotList",
                "id": "projects/fake_project/global/snapshots",
                "selfLink": "http://localhost/compute/v1beta15/projects"
                    "/fake_project/global/snapshots",
                }

        response_body = copy.deepcopy(response.json_body)
        self.assertIn("items", response_body)
        response_items = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertDictEqual(EXPECTED_SNAPSHOTS[0], response_items[0])

    def test_delete_snapshot_with_invalid_name(self):
        response = self.request_gce("/fake_project/global"
            "/snapshots/fake", method="DELETE")
        self.assertEqual(404, response.status_int)

    def test_delete_snapshot(self):
        response = self.request_gce(
                "/fake_project/global/snapshots/fake-snapshot",
                method="DELETE")
        expected = {
            "operationType": "delete",
            "targetId": "8386122516930476063",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                "fake_project/global/snapshots/fake-snapshot",
        }
        expected.update(common.COMMON_PENDING_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_create_snapshot(self):
        request_body = {
            "name": "fake-new-snapshot",
            "description": "fake description"
        }
        response = self.request_gce(
            "/fake_project/zones/nova/disks/fake-disk-3/createSnapshot",
            method="POST",
            body=request_body)
        self.assertEqual(200, response.status_int)
        expected = {
            "operationType": "createSnapshot",
            "targetId": "9202387718698825406",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/zones/nova/disks/fake-disk-3",
        }
        expected.update(common.COMMON_ZONE_PENDING_OPERATION)
        self.assertDictEqual(expected, response.json_body)
