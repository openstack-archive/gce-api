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

from gceapi.api import common as gce_common
from gceapi.api import disk_api
from gceapi.api import operation_util
from gceapi.api import scopes
from gceapi.api import snapshot_api
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Disk controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(disk_api.API(),
                                         *args, **kwargs)

    def format_item(self, request, volume, scope):
        result_dict = {
                "creationTimestamp": self._format_date(volume["created_at"]),
                "status": volume["status"],
                "name": volume["display_name"],
                "description": volume["display_description"],
                "sizeGb": volume["size"],
                }
        snapshot = volume["snapshot"]
        if snapshot:
            result_dict["sourceSnapshot"] = self._qualify(request,
                "snapshots", snapshot["display_name"],
                scopes.GlobalScope())
            result_dict["sourceSnapshotId"] = snapshot["id"]
        image_name = volume.get("image_name")
        if image_name:
            result_dict["sourceImage"] = self._qualify(request,
                "images", image_name, scopes.GlobalScope())
            result_dict["sourceImageId"] = self._get_id(
                result_dict["sourceImage"])

        return self._format_item(request, result_dict, scope)

    def create(self, req, body, scope_id):
        source_image = req.params.get("sourceImage")
        if source_image is not None:
            body["sourceImage"] = source_image
        return super(Controller, self).create(req, body, scope_id)

    def create_snapshot(self, req, body, scope_id, id):
        body["disk_name"] = id
        scope = self._get_scope(req, scope_id)
        context = self._get_context(req)
        operation_util.init_operation(context, "createSnapshot",
                                      self._type_name, id, scope)
        snapshot_api.API().add_item(context, body, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
