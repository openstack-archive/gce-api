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
from gceapi.api import scopes
from gceapi import exception


class API(base_api.API):
    """GCE Zones API."""

    KIND = "zone"
    COMPUTE_SERVICE = "nova-compute"

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        zones = self.get_items(context)
        for zone in zones:
            if zone["name"] == name:
                return zone
        raise exception.NotFound

    def get_items(self, context, scope=None):
        client = clients.nova(context)
        try:
            nova_zones = client.availability_zones.list()
        except clients.novaclient.exceptions.Forbidden as e:
            try:
                nova_zones = client.availability_zones.list(detailed=False)
            except Exception:
                raise e

        filtered_zones = list()
        for zone in nova_zones:
            if not zone.hosts:
                filtered_zones.append(zone)
                continue
            for host in zone.hosts:
                if self.COMPUTE_SERVICE in zone.hosts[host]:
                    filtered_zones.append(zone)
                    break
        zones = list()
        for zone in filtered_zones:
            zones.append({
                "name": zone.zoneName,
                "status": "UP" if zone.zoneState["available"] else "DOWN",
                "hosts": [host for host in zone.hosts]
                         if zone.hosts else list()
            })
        return zones

    def get_items_as_scopes(self, context):
        return [scopes.ZoneScope(zone["name"])
                for zone in self.get_items(context)]
