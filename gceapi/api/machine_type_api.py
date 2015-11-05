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

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import utils
from gceapi.api import zone_api
from gceapi import exception


class API(base_api.API):
    """GCE Machine types API."""

    KIND = "machineType"

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._zone_api = zone_api.API()

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        client = clients.nova(context)
        try:
            item = client.flavors.find(name=self._from_gce(name))
        except (clients.novaclient.exceptions.NotFound,
                clients.novaclient.exceptions.NoUniqueMatch):
            raise exception.NotFound
        if not item:
            raise exception.NotFound
        return self._prepare_item(utils.to_dict(item))

    def get_items(self, context, scope=None):
        client = clients.nova(context)
        items = client.flavors.list()
        return [self._prepare_item(utils.to_dict(item))
                for item in items]

    def get_scopes(self, context, item):
        # TODO(apavlov): too slow for all...
        return self._zone_api.get_items_as_scopes(context)

    def get_item_by_id(self, context, machine_type_id):
        client = clients.nova(context)
        item = client.flavors.get(machine_type_id)
        return self._prepare_item(utils.to_dict(item))

    def _prepare_item(self, item):
        item["name"] = self._to_gce(item["name"])
        return item
