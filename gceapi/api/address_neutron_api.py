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
from gceapi.api import clients
from gceapi.api import network_api
from gceapi.api import operation_util
from gceapi.api import region_api
from gceapi.api import scopes
from gceapi import exception
from gceapi.i18n import _

CONF = cfg.CONF


class API(base_api.API):
    """GCE Address API - neutron implementation."""

    KIND = "address"
    PERSISTENT_ATTRIBUTES = ["id", "creationTimestamp", "name", "description"]

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._region_api = region_api.API()

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_scopes(self, context, item):
        region = item["scope"]
        if region is not None:
            return [scopes.RegionScope(region)]
        return self._region_api.get_items_as_scopes(context)

    def get_item(self, context, name, scope=None):
        return self._get_floating_ips(context, scope, name)[0]

    def get_items(self, context, scope=None):
        return self._get_floating_ips(context, scope)

    def delete_item(self, context, name, scope=None):
        floating_ip = self._get_floating_ips(context, scope, name)[0]
        operation_util.start_operation(context)
        self._delete_db_item(context, floating_ip)
        clients.neutron(context).delete_floatingip(floating_ip["id"])

    def add_item(self, context, name, body, scope=None):
        if any(x["name"] == name
               for x in self._get_floating_ips(context, scope)):
            raise exception.InvalidInput(
                    _("The resource '%s' already exists.") % name)
        public_network_id = network_api.API().get_public_network_id(context)
        operation_util.start_operation(context)
        floating_ip = clients.neutron(context).create_floatingip(
            {"floatingip": {"floating_network_id": public_network_id}})
        floating_ip = self._prepare_floating_ip(
            clients.nova(context), floating_ip["floatingip"], scope)
        floating_ip["name"] = body["name"]
        if "description" in body:
            floating_ip["description"] = body["description"]
        floating_ip = self._add_db_item(context, floating_ip)
        return floating_ip

    def _get_floating_ips(self, context, scope, name=None):
        results = clients.neutron(context).list_floatingips(
                tenant_id=context.project_id)["floatingips"]
        gce_floating_ips = self._get_db_items_dict(context)
        nova_client = clients.nova(context)
        results = [self._prepare_floating_ip(nova_client, x, scope,
                                             gce_floating_ips.get(x["id"]))
                   for x in results]
        unnamed_ips = self._purge_db(context, results, gce_floating_ips)
        self._add_nonnamed_items(context, unnamed_ips)
        if name is None:
            return results

        for item in results:
            if item["name"] == name:
                return [item]

        raise exception.NotFound

    def _prepare_floating_ip(self, nova_client, floating_ip, scope,
                             db_item=None):
        floating_ip["scope"] = scope
        fixed_ip_address = floating_ip.get("fixed_ip_address")
        floating_ip["status"] = "IN USE" if fixed_ip_address else "RESERVED"

        if fixed_ip_address is not None:
            instances = nova_client.servers.list(
                search_opts={"fixed_ip": fixed_ip_address})
            if instances:
                floating_ip["instance_name"] = instances[0].name
                floating_ip["instance_zone"] = getattr(
                    instances[0], "OS-EXT-AZ:availability_zone")

        return self._prepare_item(floating_ip, db_item)

    def _add_nonnamed_items(self, context, items):
        for item in items:
            item["name"] = ("address-" +
                            item["floating_ip_address"].replace(".", "-"))
            item["creationTimestamp"] = ""
            self._add_db_item(context, item)
