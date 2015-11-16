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
from gceapi.api import image_api
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Image controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(image_api.API(), *args, **kwargs)

    def format_item(self, request, image, scope):
        result_dict = {
            "creationTimestamp": self._format_date(image["created_at"]),
            "name": image["name"],
            "sourceType": image["disk_format"].upper(),
            "rawDisk": {
                "containerType": "TAR",
                "source": image.get("image_ref", ""),
            },
            "status": image["status"],
            "archiveSizeBytes": str(image["size"]),
            "description": image.get("description", ""),
            # NOTE(apavlov): Size of the image when restored onto a disk.
            #"diskSizeGb": 0
        }

        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
