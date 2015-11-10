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

from oslo_config import cfg

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import image_api
from gceapi.api import operation_api
from gceapi.api import operation_util
from gceapi.api import scopes
from gceapi.api import utils
from gceapi import exception


CONF = cfg.CONF
GB = 1024 ** 3


class API(base_api.API):
    """GCE Disk API."""

    KIND = "disk"
    _status_map = {
            "creating": "CREATING",
            "downloading": "CREATING",
            "available": "READY",
            "attaching": "READY",
            "in-use": "READY",
            # "deleting": "",
            "error": "FAILED",
            # "error_deleting": "",
            "backing-up": "READY",
            "restoring-backup": "READY",
            # "error_restoring": ""
    }

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        operation_api.API().register_get_progress_method(
                "disk-add",
                self._get_add_item_progress)
        operation_api.API().register_get_progress_method(
                "disk-delete",
                self._get_delete_item_progress)

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        client = clients.cinder(context)
        volumes = client.volumes.list(search_opts={"display_name": name})
        volumes = self._filter_volumes_by_zone(volumes, scope)
        volumes = [utils.to_dict(item) for item in volumes]
        if not volumes or len(volumes) != 1:
            raise exception.NotFound
        return self._prepare_item(client, volumes[0])

    def get_items(self, context, scope=None):
        client = clients.cinder(context)
        volumes = client.volumes.list()
        volumes = self._filter_volumes_by_zone(volumes, scope)
        volumes = [utils.to_dict(item) for item in volumes]
        for volume in volumes:
            self._prepare_item(client, volume)
        return volumes

    def get_scopes(self, context, item):
        return [scopes.ZoneScope(item["availability_zone"])]

    def _prepare_item(self, client, item):
        snapshot = None
        snapshot_id = item["snapshot_id"]
        if snapshot_id:
            snapshot = utils.to_dict(client.volume_snapshots.get(snapshot_id))
        item["snapshot"] = snapshot
        item["status"] = self._status_map.get(item["status"], item["status"])
        item["name"] = item["display_name"]
        image = item.get("volume_image_metadata")
        if image:
            item["image_name"] = image["image_name"]
        return item

    def _filter_volumes_by_zone(self, volumes, scope):
        if scope is None:
            return volumes
        return filter(
            lambda volume: volume.availability_zone == scope.get_name(),
            volumes)

    def delete_item(self, context, name, scope=None):
        client = clients.cinder(context).volumes
        volumes = client.list(search_opts={"display_name": name})
        if not volumes or len(volumes) != 1:
            raise exception.NotFound
        operation_util.start_operation(context,
                                       self._get_delete_item_progress,
                                       volumes[0].id)
        client.delete(volumes[0])

    def add_item(self, context, name, body, scope=None):
        sizeGb = body.get("sizeGb")
        sizeGb = int(sizeGb) if sizeGb else None

        snapshot_uri = body.get("sourceSnapshot")
        image_uri = body.get("sourceImage")
        snapshot_id = None
        image_id = None

        client = clients.cinder(context)
        if snapshot_uri:
            snapshot_name = utils._extract_name_from_url(snapshot_uri)
            snapshots = client.volume_snapshots.list(
                search_opts={"display_name": snapshot_name})
            if not snapshots or len(snapshots) != 1:
                raise exception.NotFound
            snapshot_id = snapshots[0].id
        elif image_uri:
            image_name = utils._extract_name_from_url(image_uri)
            image = image_api.API().get_item(context, image_name, scope)
            image_id = image['id']
            # Cinder API doesn't get size from image, so we do this
            image_size_in_gb = (int(image['size']) + GB - 1) / GB
            if not sizeGb or sizeGb < image_size_in_gb:
                sizeGb = image_size_in_gb
        else:
            if not sizeGb:
                sizeGb = CONF.default_volume_size_gb

        operation_util.start_operation(context, self._get_add_item_progress)
        volume = client.volumes.create(
            sizeGb, snapshot_id=snapshot_id,
            display_name=body.get('name', name),
            display_description=body.get('description'),
            imageRef=image_id,
            availability_zone=scope.get_name())
        operation_util.set_item_id(context, volume.id, self.KIND)

        return self._prepare_item(client, utils.to_dict(volume))

    def _get_add_item_progress(self, context, volume_id):
        client = clients.cinder(context)
        try:
            volume = client.volumes.get(volume_id)
        except clients.cinderclient.exceptions.NotFound:
            return operation_util.get_final_progress()
        if (volume.status not in ["creating", "downloading"]):
            return operation_util.get_final_progress(volume.status == "error")
        return None

    def _get_delete_item_progress(self, context, volume_id):
        client = clients.cinder(context)
        try:
            volume = client.volumes.get(volume_id)
        except clients.cinderclient.exceptions.NotFound:
            return operation_util.get_final_progress()
        if volume.status not in ["deleting", "deleted"]:
            return operation_util.get_final_progress(True)
        return None
