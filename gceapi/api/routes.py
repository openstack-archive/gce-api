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
from gceapi.api import route_api
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Route controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(route_api.API(), *args, **kwargs)

    def format_item(self, request, route, scope):
        network_name = self._qualify(
                request, "global/networks", route["network"]["name"], None)
        result_dict = {
            "name": route["name"],
            "network": network_name,
            "destRange": route.get("destination"),
            "creationTimestamp": route.get("creationTimestamp", ""),
            "priority": 1000,
        }
        if "external_gateway_info" in route:
            result_dict["nextHopGateway"] = self._qualify(
                    request, "gateways", "default-internet-gateway", scope)
        else:
            nextHop = route.get("nexthop")
            if nextHop is not None:
                result_dict["nextHopIp"] = nextHop
            else:
                result_dict["nextHopNetwork"] = network_name
        if "description" in route:
            result_dict["description"] = route["description"]

        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
