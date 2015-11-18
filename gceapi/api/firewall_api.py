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

import copy

from oslo_config import cfg
from oslo_log import log as logging

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import network_api
from gceapi.api import operation_util
from gceapi.api import utils
from gceapi import exception
from gceapi.i18n import _


PROTOCOL_MAP = {
    '1': 'icmp',
    '6': 'tcp',
    '17': 'udp',
}
LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class API(base_api.API):
    """GCE Firewall API."""

    KIND = "firewall"
    PERSISTENT_ATTRIBUTES = ["id", "creationTimestamp", "network_name"]

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        network_api.API()._register_callback(
            base_api._callback_reasons.pre_delete,
            self.delete_network_firewalls)

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, name, scope=None):
        client = clients.nova(context)
        try:
            firewall = client.security_groups.find(name=name)
        except (clients.novaclient.exceptions.NotFound,
                clients.novaclient.exceptions.NoUniqueMatch):
            raise exception.NotFound()
        firewall = self._prepare_firewall(utils.to_dict(firewall))
        db_firewall = self._get_db_item_by_id(context, firewall["id"])
        self._prepare_item(firewall, db_firewall)
        return firewall

    def get_items(self, context, scope=None):
        client = clients.nova(context)
        firewalls = client.security_groups.list()
        items = list()
        gce_firewalls = self._get_db_items_dict(context)
        for firewall in firewalls:
            item = self._prepare_firewall(utils.to_dict(firewall))
            self._prepare_item(item, gce_firewalls.get(item["id"]))
            items.append(item)
        self._purge_db(context, items, gce_firewalls)
        return items

    def add_item(self, context, name, body, scope=None):
        # expected that either network is provided in parameters or
        # default network exists (as in Google)
        network = self._get_network_by_url(
            context,
            body.get('network', CONF.default_network_name)
        )
        self._check_rules(body)
        default_description = _("Firewall rules for network {}")
        group_description = body.get(
            "description",
            default_description.format(network['name'])
        )
        client = clients.nova(context)
        operation_util.start_operation(context)
        sg = client.security_groups.create(body['name'], group_description)
        try:
            rules = self._convert_to_secgroup_rules(body)
            for rule in rules:
                client.security_group_rules.create(
                    sg.id, ip_protocol=rule["protocol"],
                    from_port=rule["from_port"], to_port=rule["to_port"],
                    cidr=rule["cidr"], )
        except Exception:
            client.security_groups.delete(sg)
            raise
        new_firewall = utils.to_dict(client.security_groups.get(sg.id))
        new_firewall = self._prepare_firewall(new_firewall)
        new_firewall["network_name"] = network["name"]
        new_firewall = self._add_db_item(context, new_firewall)
        self._process_callbacks(
            context, base_api._callback_reasons.post_add, new_firewall)
        return new_firewall

    def delete_item(self, context, name, scope=None):
        firewall = self.get_item(context, name)
        operation_util.start_operation(context)
        self._process_callbacks(
            context, base_api._callback_reasons.pre_delete, firewall)
        client = clients.nova(context)
        try:
            client.security_groups.delete(firewall["id"])
            self._delete_db_item(context, firewall)
        except clients.novaclient.exceptions.ClientException as ex:
            raise exception.GceapiException(message=ex.message, code=ex.code)

    def _prepare_firewall(self, firewall):
        # NOTE(ft): OpenStack security groups are more powerful than
        # gce firewalls so when we cannot completely convert secgroup
        # we add prefixes to firewall description
        # [*] - cidr rules too complex to convert
        # [+] - non-cidr rules presents

        non_cidr_rule_exists = False
        too_complex_for_gce = False

        # NOTE(ft): group OpenStack rules by cidr and proto
        # cidr group must be comparable object
        def _ports_to_str(rule):
            if rule['from_port'] == rule['to_port']:
                return str(rule['from_port'])
            else:
                return "%s-%s" % (rule['from_port'], rule['to_port'])

        grouped_rules = {}
        for rule in firewall["rules"]:
            if "cidr" not in rule["ip_range"] or not rule["ip_range"]["cidr"]:
                non_cidr_rule_exists = True
                continue
            cidr = rule.get("ip_range", {}).get("cidr")
            proto = rule["ip_protocol"]
            cidr_group = grouped_rules.setdefault(cidr, {})
            proto_ports = cidr_group.setdefault(proto, set())
            proto_ports.add(_ports_to_str(rule))

        # NOTE(ft): compare cidr grups to understand
        # whether OpenStack rules are too complex or not
        common_rules = None
        for cidr in grouped_rules:
            if common_rules:
                if common_rules != grouped_rules[cidr]:
                    too_complex_for_gce = True
                    break
            else:
                common_rules = grouped_rules[cidr]

        # NOTE(ft): check icmp rules:
        # if per icmp type rule present then rules are too complex
        if not too_complex_for_gce and common_rules and "icmp" in common_rules:
            icmp_rules = common_rules["icmp"]
            if len(icmp_rules) == 1:
                icmp_rule = icmp_rules.pop()
                if icmp_rule != "-1":
                    too_complex_for_gce = True
            else:
                too_complex_for_gce = True

        # NOTE(ft): build gce rules if possible
        def _build_gce_port_rule(proto, rules):
            gce_rule = {"IPProtocol": proto}
            if proto != "icmp":
                gce_rule["ports"] = rules
            return gce_rule

        sourceRanges = []
        allowed = []
        if not too_complex_for_gce:
            sourceRanges = [cidr for cidr in grouped_rules] or ["0.0.0.0/0"]
            if common_rules:
                allowed = [_build_gce_port_rule(p, common_rules[p])
                           for p in common_rules]
        firewall["sourceRanges"] = sourceRanges
        firewall["allowed"] = allowed

        # NOTE(ft): add prefixes to description
        description = firewall.get("description")
        prefixes = []
        if too_complex_for_gce:
            prefixes.append("[*]")
        if non_cidr_rule_exists:
            prefixes.append("[+]")
        if prefixes:
            if description is not None:
                prefixes.append(description)
            description = "".join(prefixes)
            firewall["description"] = description

        return firewall

    def _get_network_by_url(self, context, url):
        # NOTE(apavlov): Check existence of such network
        network_name = utils._extract_name_from_url(url)
        return network_api.API().get_item(context, network_name)

    def _check_rules(self, firewall):
        if not (firewall.get('sourceRanges') or firewall.get('sourceTags')):
            msg = _("Not 'sourceRange' neither 'sourceTags' is provided")
            raise exception.InvalidRequest(msg)
        for allowed in firewall.get('allowed', []):
            proto = allowed.get('IPProtocol')
            proto = PROTOCOL_MAP.get(proto, proto)
            if not proto or proto not in PROTOCOL_MAP.values():
                msg = _("Invlaid protocol")
                raise exception.InvalidRequest(msg)
            if proto == 'icmp' and allowed.get('ports'):
                msg = _("Invalid options for icmp protocol")
                raise exception.InvalidRequest(msg)

    def _convert_to_secgroup_rules(self, firewall):
        rules = []
        for source_range in firewall['sourceRanges']:
            for allowed in firewall.get('allowed', []):
                proto = allowed['IPProtocol']
                proto = PROTOCOL_MAP.get(proto, proto)
                rule = {
                    "protocol": proto,
                    "cidr": source_range,
                }
                if proto == "icmp":
                    rule["from_port"] = -1
                    rule["to_port"] = -1
                    rules.append(rule)
                else:
                    for port in allowed.get('ports', []):
                        if "-" in port:
                            from_port, to_port = port.split("-")
                        else:
                            from_port = to_port = port
                        rule["from_port"] = from_port
                        rule["to_port"] = to_port
                        rules.append(copy.copy(rule))
        return rules

    def get_network_firewalls(self, context, network_name):
        firewalls = self.get_items(context, None)
        return [f for f in firewalls
                if f.get("network_name", None) == network_name]

    def delete_network_firewalls(self, context, network):
        network_name = network["name"]
        client = clients.nova(context)
        for secgroup in self.get_network_firewalls(context, network_name):
            try:
                client.security_groups.delete(secgroup["id"])
            except Exception:
                LOG.exception(("Failed to delete security group (%s) while"
                               "delete network (%s))"),
                              secgroup["name"], network_name)
