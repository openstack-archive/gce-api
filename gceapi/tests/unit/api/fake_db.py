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
import fixtures

from gceapi import db


ITEMS = [
    {
        "kind": "network",
        "id": "734b9c83-3a8b-4350-8fbf-d40f571ee163",
        "creationTimestamp": "2013-12-25T09:05:07.396957Z",
        "description": "main network",
    },
    {
        "kind": "route",
        "id": ("734b9c83-3a8b-4350-8fbf-d40f571ee163//"
               "eee5ba4f-c67e-40ec-8595-61b8e2bb715a//"
               "32.44.64.0/24//"
               "10.0.0.32//"
               "custom-route-1"),
        "creationTimestamp": "2013-12-25T09:05:07.396957Z",
        "description": "route for 32.44.64.0/24",
    },
    {
        "kind": "route",
        "id": ("734b9c83-3a8b-4350-8fbf-d40f571ee163//"
               "22be757a-a426-42fb-8e4b-b4c876f49f62//"
               "40.81.234.0/24//"
               "10.0.0.107//"
               "obsolete-route"),
        "creationTimestamp": "2013-12-25T09:05:07.396957Z",
        "description": "route for 40.81.234.0/24",
    },
    {
        "kind": "instance",
        "id": "d6957005-3ce7-4727-91d2-ae37fe5a199a",
        "description": "i1 description",
    },
    {
        "kind": "instance",
        "id": "6472359b-d46b-4629-83a9-d2ec8d99468c",
        "description": "i2 description",
    },
    {
        "kind": "access_config",
        "id": "i1-192.168.138.196",
        "instance_name": "i1",
        "nic": "private",
        "name": "ip for i1",
        "type": "ONE_TO_ONE_NAT",
        "addr": "192.168.138.196"
    },
    {
        "kind": "attached_disk",
        "id": "i1-ab8829ad-eec1-44a2-8068-d7f00c53ee90",
        "instance_name": "i1",
        "name": "christmas-tree",
        "volume_id": "ab8829ad-eec1-44a2-8068-d7f00c53ee90"
    },
    {
        "kind": "image",
        "id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
        "description": "christmas-tree",
        "image_ref": "http://fake_url/fake_resource"
    },
    {
        "kind": "firewall",
        "id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
        "creationTimestamp": "2013-12-25T09:01:00.396957Z",
        "network_name": "private"
    },
    {
        "kind": "firewall",
        "id": "b599598d-41b9-4075-a47e-019ba785c243",
        "creationTimestamp": "2013-12-25T09:02:00.396957Z",
        "network_name": "private"
    },
    {
        "kind": "firewall",
        "id": "1aaa637b-87f4-4e27-bc86-ff63d30264b2",
        "creationTimestamp": "2013-12-25T09:03:00.396957Z",
        "network_name": "private"
    },
    {
        "kind": "operation",
        "id": "47be73d8-b8fe-4148-9e3b-3f323136ee57",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-47be73d8-b8fe-4148-9e3b-3f323136ee57",
        "type": "add",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "zone",
        "scope_name": "nova",
        "target_type": "instance",
        "target_name": "i1",
        "method_key": "complex_operation",
        "item_id": "d6957005-3ce7-4727-91d2-ae37fe5a199a",
    },
    {
        "kind": "operation",
        "id": "fbd91157-91e9-4121-af74-090260aa38cc",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-fbd91157-91e9-4121-af74-090260aa38cc",
        "type": "delete",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "zone",
        "scope_name": "nova",
        "target_type": "instance",
        "target_name": "i-deleted",
        "method_key": "complex_operation",
        "item_id": "a6d176c9-389b-4a68-94f2-92a4cc276124",
    },
    {
        "kind": "operation",
        "id": "f6fc4e7e2-c0c8-4f97-bf1d-f6f958eb17b7",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-6fc4e7e2-c0c8-4f97-bf1d-f6f958eb17b7",
        "type": "reset",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "zone",
        "scope_name": "nova",
        "target_type": "instance",
        "target_name": "i2",
        "method_key": "instance-reset",
        "item_id": "6472359b-d46b-4629-83a9-d2ec8d99468c",
    },
    {
        "kind": "operation",
        "id": "9417e8bd-e8cc-47a1-86e8-c4c24c043b3d",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-9417e8bd-e8cc-47a1-86e8-c4c24c043b3d",
        "type": "add",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "global",
        "scope_name": None,
        "target_type": "image",
        "target_name": "fake-image-1",
        "method_key": "image-add",
        "item_id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
    },
    {
        "kind": "operation",
        "id": "0aad68c4-ee6b-45da-af7e-9e696a885168",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-0aad68c4-ee6b-45da-af7e-9e696a885168",
        "type": "delete",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "global",
        "scope_name": None,
        "target_type": "image",
        "target_name": "fake-deleted-image",
        "method_key": "image-delete",
        "item_id": "10bc8fee-401f-427b-aedc-6d7eb5e19dce",
    },
    {
        "kind": "operation",
        "id": "05e2a2b2-9708-4386-97cc-2318df3357b6",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-05e2a2b2-9708-4386-97cc-2318df3357b6",
        "type": "add",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "zone",
        "scope_name": "nova",
        "target_type": "disk",
        "target_name": "fake-disk-1",
        "method_key": "disk-add",
        "item_id": "e922ebbb-2938-4a12-869f-cbc4e26c6600",
    },
    {
        "kind": "operation",
        "id": "1cfd73fa-9b79-43ef-bbc7-c44bc514ba2e",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-1cfd73fa-9b79-43ef-bbc7-c44bc514ba2e",
        "type": "delete",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "zone",
        "scope_name": "nova",
        "target_type": "disk",
        "target_name": "fake-deleted-disk",
        "method_key": "disk-delete",
        "item_id": "7c97d368-0d8a-4833-9da0-cd58b94660c3",
    },
    {
        "kind": "operation",
        "id": "3f6f1326-3e7c-4076-be6b-939147d031ae",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-3f6f1326-3e7c-4076-be6b-939147d031ae",
        "type": "createSnapshot",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "zone",
        "scope_name": "nova",
        "target_type": "disk",
        "target_name": "fake-disk-3",
        "method_key": "snapshot-add",
        "item_id": "991cda9c-28bd-420f-8432-f5159def85d6",
    },
    {
        "kind": "operation",
        "id": "e72badca-0273-4a69-9303-181df05e602c",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "name": "operation-e72badca-0273-4a69-9303-181df05e602c",
        "type": "delete",
        "user": "admin",
        "status": "RUNNING",
        "progress": 0,
        "scope_type": "global",
        "scope_name": None,
        "target_type": "snapshot",
        "target_name": "fake-deleted-snapshot",
        "method_key": "snapshot-delete",
        "item_id": "4a354c43-4750-45cd-8d7f-643afe2946bf",
    },
    {
        "kind": "operation",
        "id": "a7b6bb82-d51f-4f04-a07c-bd9241bc2aac",
        "insert_time": "2014-01-20T11:17:39.735738Z",
        "start_time": "2014-01-20T11:17:39.935278Z",
        "end_time": "2014-01-20T11:17:43.378890Z",
        "name": "operation-a7b6bb82-d51f-4f04-a07c-bd9241bc2aac",
        "type": "setMetadata",
        "user": "admin",
        "status": "DONE",
        "progress": 100,
        "scope_type": "global",
        "scope_name": None,
        "target_type": "project",
        "target_name": None,
    },
]


class DBFixture(fixtures.Fixture):
    def __init__(self, stubs):
        super(DBFixture, self).__init__()
        self.stubs = stubs
        self.items = copy.copy(ITEMS)

    def setUp(self):
        super(DBFixture, self).setUp()
        self.stubs.Set(db, "add_item", self.fake_add_item)
        self.stubs.Set(db, "update_item", self.fake_update_item)
        self.stubs.Set(db, "delete_item", self.fake_delete_item)
        self.stubs.Set(db, "get_items", self.fake_get_items)
        self.stubs.Set(db, "get_item_by_id", self.fake_get_item_by_id)
        self.stubs.Set(db, "get_item_by_name", self.fake_get_item_by_name)

    def fake_add_item(self, context, kind, data):
        if any(item["kind"] == kind and item["id"] == data["id"] and
               (data.get("name") is None or
                item.get("name") == data.get("name") and data.get)
               for item in self.items):
            raise Exception("Duplicate entry")
        item = copy.copy(data)
        item["kind"] = kind
        self.items.append(item)
        return data

    def fake_update_item(self, context, kind, item_data):
        db_item = next((item for item in self.items
                        if (item["kind"] == kind and
                            item["id"] == item_data["id"])))
        db_item.update(item_data)

    def fake_delete_item(self, context, kind, item_id):
        self.items = [item for item in self.items
                      if item["kind"] == kind and item["id"] == item_id]

    def fake_get_items(self, context, kind):
        return [copy.copy(item) for item in self.items
                if item["kind"] == kind]

    def fake_get_item_by_id(self, context, kind, item_id):
        return next((copy.copy(item) for item in self.items
                     if item["kind"] == kind and item["id"] == item_id), None)

    def fake_get_item_by_name(self, context, kind, name):
        return next((copy.copy(item) for item in self.items
                     if item["kind"] == kind and item["name"] == name), None)
