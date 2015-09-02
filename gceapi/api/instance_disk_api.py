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

import string

from oslo_log import log as logging

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import disk_api
from gceapi.api import operation_api
from gceapi.api import operation_util
from gceapi.api import utils
from gceapi import exception
from gceapi.i18n import _

LOG = logging.getLogger(__name__)

GB = 1024 ** 3


class API(base_api.API):
    """GCE Attached disk API."""

    KIND = "attached_disk"
    PERSISTENT_ATTRIBUTES = ["id", "instance_name", "volume_id", "name",
                             "auto_delete"]

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        operation_api.API().register_get_progress_method(
                "attached_disk-delete",
                self._get_delete_item_progress)

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, instance_name, name):
        items = self._get_db_items(context)
        items = [i for i in items
                if i["instance_name"] == instance_name and i["name"] == name]
        if len(items) != 1:
            raise exception.NotFound
        return items[0]

    def get_items(self, context, instance_name):
        items = self._get_db_items(context)
        for item in items:
            item.setdefault("auto_delete", False)
        return [i for i in items if i["instance_name"] == instance_name]

    def add_item(self, context, instance_name, params, source, name,
                 auto_delete, scope):
        # NOTE(apavlov): name is a 'device_name' here
        if not name:
            msg = _("There is no name to assign.")
            raise exception.InvalidRequest(msg)

        nova_client = clients.nova(context)
        instances = nova_client.servers.list(
            search_opts={"name": instance_name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]

        devices = list()
        volumes_client = nova_client.volumes
        for server_volume in volumes_client.get_server_volumes(instance.id):
            devices.append(server_volume.device)
        device_name = None
        for letter in string.ascii_lowercase[1:]:
            device_name = "vd" + letter
            for device in devices:
                if device_name in device:
                    break
            else:
                break
        else:
            raise exception.OverQuota
        context.operation_data["device_name"] = device_name

        if source:
            volume_name = utils._extract_name_from_url(source)
            if not volume_name:
                msg = _("There is no volume to assign.")
                raise exception.NotFound(msg)
            volume = disk_api.API().get_item(context, volume_name, scope)
            context.operation_data["volume_id"] = volume["id"]
        elif params:
            params.setdefault("diskName", instance_name)
            context.operation_data["params"] = params
            context.operation_data["scope"] = scope
        else:
            msg = _('Disk config must contain either "source" or '
                    '"initializeParams".')
            raise exception.InvalidRequest(msg)

        context.operation_data["instance_id"] = instance.id
        context.operation_data["register_args"] = [instance_name, name,
                                                   auto_delete]
        operation_util.start_operation(
            context, base_api.API._get_complex_operation_progress)
        operation_util.continue_operation(
            context, lambda: self._attach_volume(context), timeout=0)

    def _attach_volume(self, context):
        params = context.operation_data.get("params")
        if params:
            scope = context.operation_data["scope"]
            context.operation_data.pop("params")
            body = {"sizeGb": params.get("diskSizeGb"),
                    "sourceImage": params["sourceImage"]}
            volume = disk_api.API().add_item(context, params.get("diskName"),
                                             body, scope=scope)
            context.operation_data["disk"] = volume
            return None

        disk = context.operation_data.get("disk")
        if disk:
            volume_id = disk["id"]
            item_progress = disk_api.API()._get_add_item_progress(context,
                                                                  volume_id)
            if not operation_util.is_final_progress(item_progress):
                return None
            context.operation_data.pop("disk")
            context.operation_data["volume_id"] = volume_id

        instance_id = context.operation_data["instance_id"]
        device_name = context.operation_data["device_name"]
        volume_id = context.operation_data["volume_id"]
        volumes_client = clients.nova(context).volumes
        volumes_client.create_server_volume(
                instance_id, volume_id, "/dev/" + device_name)

        args = context.operation_data["register_args"]
        self.register_item(context, args[0], volume_id, args[1], args[2])

        return operation_util.get_final_progress()

    def register_item(self, context, instance_name, volume_id, name,
                      auto_delete):
        if not name:
            msg = _("There is no name to assign.")
            raise exception.InvalidRequest(msg)
        if not volume_id:
            msg = _("There is no volume_id to assign.")
            raise exception.InvalidRequest(msg)

        new_item = {
            "id": instance_name + "-" + volume_id,
            "instance_name": instance_name,
            "volume_id": volume_id,
            "name": name,
            "auto_delete": auto_delete
        }
        new_item = self._add_db_item(context, new_item)
        return new_item

    def delete_item(self, context, instance_name, name):
        item = self.get_item(context, instance_name, name)
        volume_id = item["volume_id"]

        nova_client = clients.nova(context)
        instances = nova_client.servers.list(
            search_opts={"name": instance_name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]

        operation_util.start_operation(context,
                                       self._get_delete_item_progress,
                                       item["id"])
        nova_client.volumes.delete_server_volume(instance.id, volume_id)

        self._delete_db_item(context, item)

    def set_disk_auto_delete(self, context, instance_name, name, auto_delete):
        item = self.get_item(context, instance_name, name)
        item["auto_delete"] = auto_delete
        self._update_db_item(context, item)

    def unregister_item(self, context, instance_name, name):
        item = self.get_item(context, instance_name, name)
        self._delete_db_item(context, item)

    def _get_add_item_progress(self, context, dummy_id):
        return operation_util.get_final_progress()

    def _get_delete_item_progress(self, context, dummy_id):
        return operation_util.get_final_progress()
