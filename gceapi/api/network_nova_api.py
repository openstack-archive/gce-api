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

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import operation_util
from gceapi.api import utils
from gceapi import exception
from gceapi.i18n import _


CONF = cfg.CONF


class API(base_api.API):
    """GCE Network API - nova-network implementation."""

    KIND = "network"
    PERSISTENT_ATTRIBUTES = ["id", "creationTimestamp", "description"]

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, name, scope=None):
        client = clients.nova(context)
        try:
            network = client.networks.find(label=name)
        except clients.novaclient.exceptions.NotFound:
            msg = _("Network resource '%s' could not be found.") % name
            raise exception.NotFound(msg)
        gce_network = self._get_db_item_by_id(context, network.id)
        return self._prepare_network(utils.to_dict(network), gce_network)

    def get_items(self, context, scope=None):
        client = clients.nova(context)
        networks = client.networks.list()
        gce_networks = self._get_db_items_dict(context)
        result_networks = []
        for network in networks:
            result_networks.append(
                    self._prepare_network(utils.to_dict(network),
                                          gce_networks.get(network.id)))
        self._purge_db(context, result_networks, gce_networks)
        return result_networks

    def delete_item(self, context, name, scope=None):
        network = self.get_item(context, name)
        self._process_callbacks(
            context, base_api._callback_reasons.check_delete, network)
        operation_util.start_operation(context)
        self._delete_db_item(context, network)
        self._process_callbacks(
            context, base_api._callback_reasons.pre_delete, network)
        client = clients.nova(context)
        client.networks.delete(network["id"])

    def add_item(self, context, name, body, scope=None):
        ip_range = body.get('IPv4Range', CONF.default_network_ip_range)
        gateway = body.get('gatewayIPv4')
        if gateway is None:
            network_cidr = netaddr.IPNetwork(ip_range)
            gateway_ip = netaddr.IPAddress(network_cidr.first + 1)
            gateway = str(gateway_ip)
        network = None
        try:
            network = self.get_item(context, name)
        except exception.NotFound:
            pass
        if network is not None:
            raise exception.DuplicateVlan
        kwargs = {'label': name, 'cidr': ip_range, 'gateway': gateway}
        client = clients.nova(context)
        operation_util.start_operation(context)
        network = client.networks.create(**kwargs)
        network = self._prepare_network(utils.to_dict(network))
        if "description" in body:
            network["description"] = body["description"]
        return self._add_db_item(context, network)

    def _prepare_network(self, network, db_data=None):
        return self._prepare_item({
                'name': network['label'],
                'IPv4Range': network['cidr'],
                'gatewayIPv4': network['gateway'],
                'id': network['id']},
            db_data)
