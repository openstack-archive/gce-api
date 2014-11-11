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
from gceapi.api import region_api
from gceapi.api import wsgi as gce_wsgi
from gceapi.api import zone_api


class Controller(gce_common.Controller):
    """GCE Regions controller."""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(region_api.API(), *args, **kwargs)
        self._zone_api = zone_api.API()

    def format_item(self, req, region, scope):
        zones = self._zone_api.get_items(self._get_context(req), scope)
        result_dict = {
            "name": region["name"],
            "status": "UP",
            "zones": [self._qualify(req, "zones", zone["name"], None)
                      for zone in zones]
        }

        return self._format_item(req, result_dict, scope)


def create_resource():
    return gce_wsgi.GCEResource(Controller())
