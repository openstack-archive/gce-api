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
from gceapi.api import network_api
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Network controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(network_api.API(), *args, **kwargs)

    def format_item(self, request, network, scope):
        result_dict = {
            "name": network["name"],
            "IPv4Range": network.get("IPv4Range", ""),
            "gatewayIPv4": network.get("gatewayIPv4", ""),
            "creationTimestamp": network.get("creationTimestamp", ""),
        }
        description = network.get("description")
        if description is not None:
            result_dict["description"] = description

        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
