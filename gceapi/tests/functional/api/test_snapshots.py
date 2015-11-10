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

from gceapi.tests.functional.api import test_disks


class TestSnapshots(test_disks.TestDiskBase):
    def test_list_snapshots(self):
        # prepare object for listing
        data = self._create_disk_and_snapshot()
        disk_name = data['disk']['name']
        snapshot = data['snapshot']
        snapshot_name = snapshot['name']
        # list and find object from server and check properties
        result = self._list_snapshots()
        result = self.assertFind(snapshot_name, result)
        self.assertObject(snapshot, result)
        self._delete_snapshot(snapshot_name)
        self._delete_disk(disk_name)

    def test_list_snapshots_by_filter_name(self):
        # prepare objects for listings
        objects = list()
        for i in range(0, 3):
            objects.append(self._create_disk_and_snapshot())
        # list snapshots with filter by name
        for item in objects:
            snapshot = item['snapshot']
            snapshot_filter = 'name eq {}'.format(snapshot['name'])
            result = self._list_snapshots(filter=snapshot_filter)
            self.assertEqual(1, len(result['items']))
            self.assertObject(snapshot, result['items'][0])
        # clean resources
        for item in objects:
            self._delete_snapshot(item['snapshot']['name'])
            self._delete_disk(item['disk']['name'])
