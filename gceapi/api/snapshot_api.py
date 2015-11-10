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

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import operation_api
from gceapi.api import operation_util
from gceapi.api import utils
from gceapi import exception


class API(base_api.API):
    """GCE Snapshot API."""

    KIND = "snapshot"
    _status_map = {
        'creating': 'CREATING',
        'available': 'READY',
        'active': 'READY',
        'deleting': 'DELETING',
        'deleted': 'DELETING',
        'error': 'FAILED'}

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        operation_api.API().register_get_progress_method(
                "snapshot-add",
                self._get_add_item_progress)
        operation_api.API().register_get_progress_method(
                "snapshot-delete",
                self._get_delete_item_progress)

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        client = clients.cinder(context)
        snapshots = client.volume_snapshots.list(
            search_opts={"display_name": name})
        if snapshots and len(snapshots) == 1:
            return self._prepare_item(client, utils.to_dict(snapshots[0]))
        raise exception.NotFound

    def get_items(self, context, scope=None):
        client = clients.cinder(context)
        snapshots = [utils.to_dict(item)
                     for item in client.volume_snapshots.list()]
        for snapshot in snapshots:
            self._prepare_item(client, snapshot)
        return snapshots

    def delete_item(self, context, name, scope=None):
        client = clients.cinder(context).volume_snapshots
        snapshots = client.list(search_opts={"display_name": name})
        if not snapshots or len(snapshots) != 1:
            raise exception.NotFound
        operation_util.start_operation(context,
                                       self._get_delete_item_progress,
                                       snapshots[0].id)
        client.delete(snapshots[0])

    def add_item(self, context, body, scope=None):
        name = body["name"]
        disk_name = body["disk_name"]
        client = clients.cinder(context)
        volumes = client.volumes.list(search_opts={"display_name": disk_name})
        if not volumes or len(volumes) != 1:
            raise exception.NotFound

        operation_util.start_operation(context, self._get_add_item_progress)
        snapshot = client.volume_snapshots.create(
            volumes[0].id, True, name, body.get("description"))
        operation_util.set_item_id(context, snapshot.id, self.KIND)

        return self._prepare_item(client, utils.to_dict(snapshot))

    def _prepare_item(self, client, item):
        item["name"] = item["display_name"]
        try:
            item["disk"] = utils.to_dict(client.volumes.get(item["volume_id"]))
        except Exception:
            pass
        item["status"] = self._status_map.get(item["status"], item["status"])
        return item

    def _get_add_item_progress(self, context, snapshot_id):
        client = clients.cinder(context)
        try:
            snapshot = client.volume_snapshots.get(snapshot_id)
        except clients.cinderclient.exceptions.NotFound:
            return operation_util.get_final_progress()
        if (snapshot.status != "creating"):
            return operation_util.get_final_progress(snapshot.status
                                                     == "error")
        return None

    def _get_delete_item_progress(self, context, snapshot_id):
        client = clients.cinder(context)
        try:
            snapshot = client.volume_snapshots.get(snapshot_id)
        except clients.cinderclient.exceptions.NotFound:
            return operation_util.get_final_progress()
        if snapshot.status not in ["deleting", "deleted"]:
            return operation_util.get_final_progress(True)
        return None
