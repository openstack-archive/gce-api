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

try:
    from glanceclient import exc as glanceclient_exc
except ImportError:
    glanceclient_exc = None

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import operation_api
from gceapi.api import operation_util
from gceapi.api import utils
from gceapi import exception
from gceapi.i18n import _


class API(base_api.API):
    """GCE Image API."""

    KIND = "image"
    PERSISTENT_ATTRIBUTES = ["id", "description", "image_ref"]

    _status_map = {
        "queued": "PENDING",
        "saving": "PENDING",
        "active": "READY",
        "killed": "FAILED",
        # "deleted": "",
        # "pending_delete": ""
    }

    _deleted_statuses = ["deleted", "pending_delete"]

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        operation_api.API().register_get_progress_method(
                "image-add",
                self._get_add_item_progress)
        operation_api.API().register_get_progress_method(
                "image-delete",
                self._get_delete_item_progress)

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, name, scope=None):
        image_service = clients.glance(context).images
        images = image_service.list(
            filters={"name": name, "disk_format": "raw"})
        result = None
        for image in images:
            if image.status in self._deleted_statuses:
                continue
            if result:
                msg = _("Image resource '%s' found more than once") % name
                raise exception.NotFound(msg)
            result = self._prepare_image(utils.to_dict(image))
            db_image = self._get_db_item_by_id(context, result["id"])
            self._prepare_item(result, db_image)
        if not result:
            msg = _("Image resource '%s' could not be found") % name
            raise exception.NotFound(msg)
        return result

    def get_items(self, context, scope=None):
        image_service = clients.glance(context).images
        # NOTE(apavlov): Currently glance doesn't report "killed" images in
        # list which causes incompatibility with GCE which reports
        # corresponding "FAILED" images if upload has failed.
        images = image_service.list(filters={"disk_format": "raw"})
        items = list()
        gce_images = self._get_db_items_dict(context)
        for image in images:
            result = self._prepare_image(utils.to_dict(image))
            self._prepare_item(result, gce_images.get(result["id"]))
            items.append(result)
        self._purge_db(context, items, gce_images)
        return items

    def _prepare_image(self, item):
        item["status"] = self._status_map.get(item["status"], item["status"])
        return item

    def delete_item(self, context, name, scope=None):
        """Delete an image, if allowed."""
        image = self.get_item(context, name, scope)
        image_service = clients.glance(context).images
        operation_util.start_operation(context,
                                       self._get_delete_item_progress,
                                       image["id"])
        image_service.delete(image["id"])
        self._delete_db_item(context, image)

    def add_item(self, context, name, body, scope=None):
        name = body['name']
        image_ref = body['rawDisk']['source']
        meta = {
            'name': name,
            'disk_format': 'raw',
            'container_format': 'bare',
            'min_disk': 0,
            'min_ram': 0,
            'copy_from': image_ref,
        }
        image_service = clients.glance(context).images
        operation_util.start_operation(context, self._get_add_item_progress)
        image = image_service.create(**meta)
        operation_util.set_item_id(context, image.id, self.KIND)

        new_image = self._prepare_image(utils.to_dict(image))
        new_image["description"] = body.get("description", "")
        new_image["image_ref"] = image_ref
        new_image = self._add_db_item(context, new_image)
        return new_image

    def _get_add_item_progress(self, context, image_id):
        image_service = clients.glance(context).images
        try:
            image = image_service.get(image_id)
        except glanceclient_exc.HTTPNotFound:
            return operation_util.get_final_progress()
        if image.status not in ["queued", "saving"]:
            return operation_util.get_final_progress(image.status == "killed")
        return None

    def _get_delete_item_progress(self, context, image_id):
        image_service = clients.glance(context).images
        try:
            image = image_service.get(image_id)
            if image.status in self._deleted_statuses:
                return operation_util.get_final_progress()
        except glanceclient_exc.HTTPNotFound:
            return operation_util.get_final_progress()
        return None
