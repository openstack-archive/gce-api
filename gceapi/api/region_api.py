#    Copyright 2013 Cloudscaling Group, Inc
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from gceapi.api import base_api
from gceapi.api import scopes
from gceapi import exception


class API(base_api.API):
    """GCE Regions API

    Stubbed now for support only one predefined region nova
    """

    KIND = "region"
    _REGIONS = ["nova"]

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        regions = self.get_items(context)
        for region in regions:
            if region["name"] == name:
                return region
        raise exception.NotFound

    def get_items(self, context, scope=None):
        return [{"name": region for region in self._REGIONS}]

    def get_items_as_scopes(self, context):
        return [scopes.RegionScope(region) for region in self._REGIONS]
