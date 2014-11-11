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
from gceapi.api import firewall_api
from gceapi.api import scopes
from gceapi.api import wsgi as gce_wsgi


class Controller(gce_common.Controller):
    """GCE Firewall controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(firewall_api.API(), *args, **kwargs)

    def format_item(self, request, firewall, scope):
        result_dict = {
            "creationTimestamp": firewall.get("creationTimestamp", ""),
            "name": firewall["name"],
            "description": firewall["description"],
            "sourceRanges": firewall["sourceRanges"],
            "allowed": firewall["allowed"],
        }

        network = firewall.get("network_name")
        if network:
            result_dict["network"] = self._qualify(request,
                "networks", network, scopes.GlobalScope())

        return self._format_item(request, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
