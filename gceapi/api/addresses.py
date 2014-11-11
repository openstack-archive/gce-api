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

from gceapi.api import address_api
from gceapi.api import common as gce_common
from gceapi.api import scopes
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Address controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(address_api.API(),
                                         *args, **kwargs)

    def format_item(self, request, floating_ip, scope):
        result_dict = {
            "creationTimestamp": floating_ip.get("creationTimestamp", ""),
            "status": floating_ip["status"],
            "name": floating_ip["name"],
            "address": floating_ip["floating_ip_address"],
        }
        if "description" in floating_ip:
            result_dict["description"] = floating_ip["description"]
        else:
            result_dict["description"] = ""

        if "instance_name" in floating_ip:
            result_dict["users"] = [self._qualify(
                request, "instances", floating_ip["instance_name"],
                scopes.ZoneScope(floating_ip["instance_zone"]))]

        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
