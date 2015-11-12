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

import netaddr
from oslo_config import cfg
from oslo_log import log as logging

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import operation_util
from gceapi import exception
from gceapi.i18n import _


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Network API - neutron implementation."""

    KIND = "network"
    PERSISTENT_ATTRIBUTES = ["id", "creationTimestamp", "description"]

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        self._public_network_name = CONF.public_network

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, name, scope=None):
        client = clients.neutron(context)
        networks = client.list_networks(
            tenant_id=context.project_id, name=name)["networks"]
        if not networks:
            msg = _("Network resource '%s' could not be found.") % name
            raise exception.NotFound(msg)
        else:
            # NOTE(Alex) There might be more than one network with this name.
            # TODO(Alex) We have to decide if we should support IDs as
            # parameters for names as well and return error if we have
            # multi-results when addressed by name.
            network = networks[0]
            gce_network = self._get_db_item_by_id(context, network["id"])
            return self._prepare_network(client, network, gce_network)

    def get_items(self, context, scope=None):
        client = clients.neutron(context)
        networks = client.list_networks(tenant_id=context.project_id)
        networks = networks["networks"]
        gce_networks = self._get_db_items_dict(context)
        result_networks = []
        for network in networks:
            network = self._prepare_network(client, network,
                                            gce_networks.get(network["id"]))
            result_networks.append(network)
        self._purge_db(context, result_networks, gce_networks)
        return result_networks

    def delete_item(self, context, name, scope=None):
        client = clients.neutron(context)
        network = self.get_item(context, name)

        self._process_callbacks(
            context, base_api._callback_reasons.check_delete, network)
        operation_util.start_operation(context)
        self._delete_db_item(context, network)
        self._process_callbacks(
            context, base_api._callback_reasons.pre_delete, network)

        client.delete_network(network["id"])

    def add_item(self, context, name, body, scope=None):
        ip_range = body.get('IPv4Range', CONF.default_network_ip_range)
        gateway = body.get('gatewayIPv4')
        if gateway is None:
            network_cidr = netaddr.IPNetwork(ip_range)
            gateway_ip = netaddr.IPAddress(network_cidr.first + 1)
            gateway = str(gateway_ip)
        client = clients.neutron(context)
        network = None
        try:
            network = self.get_item(context, name)
        except exception.NotFound:
            pass
        if network is not None:
            raise exception.DuplicateVlan
        network_body = {}
        network_body["network"] = {"name": name}
        operation_util.start_operation(context)
        network = client.create_network(network_body)
        network = network["network"]
        if ip_range:
            subnet_body = {}
            subnet_body["subnet"] = {
                # NOTE(Alex) "name": name + ".default_subnet",
                # Won't give it a name for now
                "network_id": network["id"],
                "ip_version": "4",
                "cidr": ip_range,
                "gateway_ip": gateway}
            result_data = client.create_subnet(subnet_body)
            subnet_id = result_data["subnet"]["id"]
        network = self._prepare_network(client, network)
        if 'description' in body:
            network["description"] = body["description"]
        network = self._add_db_item(context, network)
        self._process_callbacks(
            context, base_api._callback_reasons.post_add,
            network, subnet_id=subnet_id)
        return network

    def _prepare_network(self, client, network, db_network=None):
        subnets = network['subnets']
        if subnets and len(subnets) > 0:
            subnet = client.show_subnet(subnets[0])
            subnet = subnet["subnet"]
            network["subnet_id"] = subnet["id"]
            network["IPv4Range"] = subnet.get("cidr", None)
            network["gatewayIPv4"] = subnet.get("gateway_ip", None)
        return self._prepare_item(network, db_network)

    def get_public_network_id(self, context):
        """Get id of public network appointed to GCE in config."""
        client = clients.neutron(context)
        search_opts = {"name": self._public_network_name,
                       "router:external": True}
        networks = client.list_networks(**search_opts)["networks"]
        return networks[0]["id"]
