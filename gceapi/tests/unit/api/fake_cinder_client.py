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

from cinderclient import exceptions as exc

from gceapi.tests.unit.api import fake_request
from gceapi.tests.unit.api import utils


FAKE_DISKS = [utils.FakeObject({
    "status": "available",
    "volume_type": None,
    "display_name": "fake-disk-1",
    "availability_zone": "nova",
    "created_at": "2013-08-14T12:35:22.000000",
    "display_description": "fake disk from snapshot",
    "metadata": {},
    "snapshot_id": "991cda9c-28bd-420f-8432-f5159def85d6",
    "id": "e922ebbb-2938-4a12-869f-cbc4e26c6600",
    "size": 2,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
    "attachments": [],
}), utils.FakeObject({
    "status": "available",
    "volume_type": None,
    "bootable": u"true",
    "volume_image_metadata": {
        "image_id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
        "image_name": "fake-image-1"
    },
    "display_name": "fake-disk-2",
    "availability_zone": "nova",
    "created_at": "2013-08-14T12:19:35.000000",
    "display_description": "",
    "metadata": {},
    "snapshot_id": None,
    "id": "64ebe1d9-757f-4074-88d0-2ac790be909d",
    "size": 1,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
    "attachments": [],
}), utils.FakeObject({
    "status": "available",
    "volume_type": None,
    "display_name": "fake-disk-3",
    "availability_zone": "nova",
    "created_at": "2013-08-14T11:57:44.000000",
    "display_description": "full description of disk",
    "metadata": {},
    "snapshot_id": None,
    "id": "fc0d5c01-dc3b-450d-aaed-de028bb832b1",
    "size": 3,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
    "attachments": [],
}), utils.FakeObject({
    "status": "available",
    "volume_type": None,
    "display_name": "disk-to-delete",
    "availability_zone": "nova",
    "created_at": "2013-08-14T12:10:02.000000",
    "display_description": "full description of disk",
    "metadata": {},
    "snapshot_id": None,
    "id": "a0786ec1-d838-4ad6-a497-87ec0b79161b",
    "size": 3,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
    "attachments": [],
}), utils.FakeObject({
    "status": "in-use",
    "instance_uuid": "6472359b-d46b-4629-83a9-d2ec8d99468c",
    "bootable": u"true",
    "volume_image_metadata": {
        "image_id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
        "image_name": "fake-image-1"},
    "display_name": "i1",
    "availability_zone": "nova",
    "created_at": "2013-08-14T18:55:57.000000",
    "display_description": "Persistent boot disk created from "
        "http://127.0.0.1:8787/compute/v1beta15/projects/admin"
        "/global/images/fake-image-1.",
    "volume_type": "None",
    "metadata": {},
    "snapshot_id": None,
    "id": "ab8829ad-eec1-44a2-8068-d7f00c53ee90",
    "size": 1,
    "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
    "os-vol-mig-status-attr:name_id": None,
    "os-vol-mig-status-attr:migstat": None,
    "os-vol-host-attr:host": "grizzly",
    "attachments": [{
        "device": "vdc",
        "server_id": "6472359b-d46b-4629-83a9-d2ec8d99468c",
        "volume_id": "ab8829ad-eec1-44a2-8068-d7f00c53ee90",
        "host_name": None,
        "id": "7f862e44-5f41-4a1f-b2f8-dbd2f6bef86f"
    }],
})]

FAKE_SNAPSHOTS = [utils.FakeObject({
    "status": "available",
    "display_name": "fake-snapshot",
    "created_at": "2013-08-14T12:32:28.000000",
    "display_description": "full description of snapshot 1",
    "volume_size": 2,
    "volume_id": "fc0d5c01-dc3b-450d-aaed-de028bb832b1",
    "progress": "100%",
    "project_id": "f0dcd67240544bc6903766a025c6e2b9",
    "id": "991cda9c-28bd-420f-8432-f5159def85d6",
    "size": 2,
})]

FAKE_NEW_DISKS = {
    "new-disk": {
        "status": "available",
        "volume_type": None,
        "availability_zone": "nova",
        "created_at": "2013-08-14T15:00:22.000000",
        "display_description": "",
        "metadata": {},
        "snapshot_id": None,
        "id": "8af36778-84db-475e-b3c9-da2cc260df4a",
        "size": 1,
        "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
        "os-vol-mig-status-attr:name_id": None,
        "os-vol-mig-status-attr:migstat": None,
        "os-vol-host-attr:host": "grizzly",
        "attachments": [],
    },
    "new-image-disk": {
        "status": "available",
        "volume_type": None,
        "bootable": u"true",
        "volume_image_metadata": {
            "image_id": "a2459075-d96c-40d5-893e-577ff92e721c",
            "image_name": "fake-image-2"
        },
        "availability_zone": "nova",
        "created_at": "2013-08-14T15:56:00.000000",
        "display_description": "disk created with image",
        "metadata": {},
        "snapshot_id": None,
        "id": "f35151b8-7b81-4e76-b2ab-ecdc14f949d2",
        "size": 1,
        "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
        "os-vol-mig-status-attr:name_id": None,
        "os-vol-mig-status-attr:migstat": None,
        "os-vol-host-attr:host": "grizzly",
        "attachments": [],
    },
    "new-sn-disk": {
        "status": "creating",
        "volume_type": "None",
        "availability_zone": "nova",
        "created_at": "2013-08-14T16:43:59.000000",
        "display_description": "disk created from snapshot",
        "metadata": {},
        "snapshot_id": "991cda9c-28bd-420f-8432-f5159def85d6",
        "id": "ae2de9eb-32f2-4db7-8ef0-23f0fd0ebf63",
        "size": 1,
        "os-vol-tenant-attr:tenant_id": fake_request.PROJECT_ID,
        "os-vol-mig-status-attr:name_id": None,
        "os-vol-mig-status-attr:migstat": None,
        "os-vol-host-attr:host": "grizzly",
        "attachments": [],
    },
}


FAKE_QUOTAS = utils.FakeObject({
    "gigabytes": {
        "limit": 1000,
        "reserved": 0,
        "in_use": 2
    },
    "snapshots": {
        "limit": 10,
        "reserved": 0,
        "in_use": 1
    },
    "human_id": None,
    "volumes": {
        "limit": 10,
        "reserved": 0,
        "in_use": 1
    },
    "HUMAN_ID": False
})


class FakeVolumes(object):
    def list(self, detailed=True, search_opts=None):
        result = FAKE_DISKS
        if search_opts:
            if "display_name" in search_opts:
                result = [d for d in result
                    if d.display_name == search_opts["display_name"]]
        return result

    def get(self, disk):
        disk_id = utils.get_id(disk)
        for disk in FAKE_DISKS:
            if disk.id == disk_id:
                return disk
        raise exc.NotFound(exc.NotFound.http_status)

    def delete(self, volume):
        global FAKE_DISKS
        volume_id = utils.get_id(volume)
        FAKE_DISKS = [v for v in FAKE_DISKS if v.id != volume_id]

    def create(self, size, snapshot_id=None, source_volid=None,
            display_name=None, display_description=None,
            volume_type=None, user_id=None,
            project_id=None, availability_zone=None,
            metadata=None, imageRef=None):
        volume = copy.deepcopy(FAKE_NEW_DISKS[display_name])
        volume["display_name"] = display_name
        volume["availability_zone"] = availability_zone
        volume["display_description"] = display_description
        volume["size"] = size
        if project_id:
            volume["os-vol-tenant-attr:tenant_id"] = project_id
        if snapshot_id is not None:
            volume["snapshot_id"] = snapshot_id
        if imageRef is not None:
            volume["volume_image_metadata"] = {
                "image_id": imageRef,
                "image_name": "fake-image-2"
            }
        FAKE_DISKS.append(utils.FakeObject(volume))
        return utils.FakeObject(volume)


class FakeVolumeSnapshots(object):
    def get(self, snapshot):
        snapshot_id = utils.get_id(snapshot)
        for snapshot in FAKE_SNAPSHOTS:
            if snapshot.id == snapshot_id:
                return snapshot
        raise exc.NotFound(exc.NotFound.http_status)

    def list(self, detailed=True, search_opts=None):
        result = FAKE_SNAPSHOTS
        if search_opts:
            if "display_name" in search_opts:
                result = [d for d in result
                    if d.display_name == search_opts["display_name"]]
        return result

    def delete(self, snapshot):
        pass

    def create(self, volume_id, force=False,
               display_name=None, display_description=None):
        return FAKE_SNAPSHOTS[0]


class FakeQuotas(object):
    def get(self, tenant_id, **kwargs):
        if "usage" not in kwargs:
            raise exc.BadRequest("There is no arg 'usage' in request")
        return FAKE_QUOTAS


class FakeCinderClient(object):
    def __init__(self, version, *args, **kwargs):
        pass

    @property
    def client(self):
        return self

    @property
    def volumes(self):
        return FakeVolumes()

    @property
    def volume_snapshots(self):
        return FakeVolumeSnapshots()

    @property
    def quotas(self):
        return FakeQuotas()
