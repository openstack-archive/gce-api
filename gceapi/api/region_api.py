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

from oslo_config import cfg

from gceapi.api import base_api
from gceapi.api import scopes
from gceapi import exception

CONF = cfg.CONF

# OS usual region names are in PascalCase - e.g. RegionOne,
# GCE region name should matche the regexp [a-z](?:[-a-z0-9]{0,61}[a-z0-9])?
_OS_GCE_MAP = {
    'RegionOne': 'region-one',
    'RegionTwo': 'region-two',
    'RegionThree': 'region-three',
    'RegionFour': 'region-four',
}


def _map_region_name(name):
    return _OS_GCE_MAP.get(name, name)


class API(base_api.API):
    """GCE Regions API

    Stubbed now for support only one predefined region from config
    #TODO(apavlov): need to implement discovering or regions from keystone
    """

    KIND = "region"
    _REGIONS = []

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._REGIONS = [_map_region_name(CONF.get("region").strip())]

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        regions = self.get_items(context)
        for region in regions:
            if region["name"] == name:
                return region
        raise exception.NotFound

    def get_items(self, context, scope=None):
        return [dict(("name", region) for region in self._REGIONS)]

    def get_items_as_scopes(self, context):
        return [scopes.RegionScope(region) for region in self._REGIONS]
