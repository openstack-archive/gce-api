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
import uuid

from gceapi.tests.unit.api import fake_request


FAKE_NETWORKS = {
    'networks': [{
        u'status': u'ACTIVE',
        u'subnets': [u'cd84a13b-6246-424f-9dd2-04c324ed4da0'],
        u'name': u'private',
        u'provider:physical_network': None,
        u'admin_state_up': True,
        u'tenant_id': fake_request.PROJECT_ID,
        u'provider:network_type': u'local',
        u'router:external': False,
        u'shared': False,
        u'id': u'734b9c83-3a8b-4350-8fbf-d40f571ee163',
        u'provider:segmentation_id': None
    }, {
        u'status': u'ACTIVE',
        u'subnets': [u'7a2800b8-0e66-4271-b26c-6af01dcba66f'],
        u'name': u'public',
        u'provider:physical_network': None,
        u'admin_state_up': True,
        u'tenant_id': fake_request.PROJECT_ID,
        u'provider:network_type': u'local',
        u'router:external': True,
        u'shared': False,
        u'id': u'7aa33661-33ba-4291-a2c7-44bfd59884c1',
        u'provider:segmentation_id': None
    }, {
        u'status': u'ACTIVE',
        u'subnets': [],
        u'name': u'public',
        u'provider:physical_network': None,
        u'admin_state_up': True,
        u'tenant_id': u'ae7d3f067c3c4243bb0c6ea0fa8fb6e4',
        u'provider:network_type': u'local',
        u'router:external': True,
        u'shared': False,
        u'id': u'439fa4f9-cdd7-4ee2-b3cf-5e764cf644af',
        u'provider:segmentation_id': None
    },
]}

FAKE_SUBNETS = [{
    u'subnet': {
        u'name': u'',
        u'enable_dhcp': True,
        u'network_id': u'734b9c83-3a8b-4350-8fbf-d40f571ee163',
        u'tenant_id': fake_request.PROJECT_ID,
        u'dns_nameservers': [],
        u'allocation_pools': [{
            u'start': u'10.0.0.2',
            u'end': u'10.0.0.254'
        }],
        u'host_routes': [],
        u'ip_version': 4,
        u'gateway_ip': u'10.0.0.1',
        u'cidr': u'10.0.0.0/24',
        u'id': u'cd84a13b-6246-424f-9dd2-04c324ed4da0'
    }
}, {
    u'subnet': {
        u'name': u'',
        u'enable_dhcp': False,
        u'network_id': u'7aa33661-33ba-4291-a2c7-44bfd59884c1',
        u'tenant_id': u'ae7d3f067c3c4243bb0c6ea0fa8fb6e4',
        u'dns_nameservers': [],
        u'allocation_pools': [{
            u'start': u'172.24.4.226',
            u'end': u'172.24.4.238'
        }],
        u'host_routes': [],
        u'ip_version': 4,
        u'gateway_ip': u'172.24.4.225',
        u'cidr': u'172.24.4.224/28',
        u'id': u'7a2800b8-0e66-4271-b26c-6af01dcba66f'
    }
}]

FAKE_ROUTERS = [{
    u'id': u'45d8de89-0e40-4d9d-977f-db3573a6e7cf',
    u'tenant_id': fake_request.PROJECT_ID,
    u'external_gateway_info': {
        "network_id": u'503b83b5-bec0-4071-b8ba-789595c8f7b2'
    },
    u'routes': [{
        u'destination': u'32.44.64.0/24',
        u'nexthop': u'10.0.0.32'
    }, {
        u'destination': u'89.34.0.0/16',
        u'nexthop': u'10.0.0.78'
    }],
}]

FAKE_PORTS = [{
    u'id': u'3e10c6ac-9fcc-492d-95fb-1b7ea93529f2',
    u'tenant_id': fake_request.PROJECT_ID,
    u'device_owner': u'network:router_gateway',
    u'network_id': u'503b83b5-bec0-4071-b8ba-789595c8f7b2',
    u'device_id': u'45d8de89-0e40-4d9d-977f-db3573a6e7cf',
}, {
    u'id': u'eee5ba4f-c67e-40ec-8595-61b8e2bb715a',
    u'tenant_id': fake_request.PROJECT_ID,
    u'device_owner': u'network:router_interface',
    u'network_id': u'734b9c83-3a8b-4350-8fbf-d40f571ee163',
    u'device_id': u'45d8de89-0e40-4d9d-977f-db3573a6e7cf',
    u'fixed_ips': [{
        u'subnet_id': u'cd84a13b-6246-424f-9dd2-04c324ed4da0'
    }],
}]


FAKE_ADDRESSES = {
    "floatingips": [{
        u"fixed_ip_address": u"192.168.138.196",
        u"floating_ip_address": u"172.24.4.227",
        u"floating_network_id": u"7aa33661-33ba-4291-a2c7-44bfd59884c1",
        u"id": u"81c45d28-3699-4116-bacd-7488996c5293",
        u"port_id": u"8984b23b-f945-4b1e-8eb0-7e735285c0cc",
        u"router_id": u"59e96d7b-749d-433e-b592-a55ba94b935e",
        u"tenant_id": fake_request.PROJECT_ID
    }]
}


FAKE_QUOTAS = {
    "quota": {
        "subnet": 10,
        "network": 10,
        "floatingip": 50,
        "security_group_rule": 100,
        "security_group": 10,
        "router": 10,
        "port": 50
    }
}


FAKE_SECURITY_GROUPS = {
    "security_groups": [{}, {}]
}


class FakeNeutronClient(object):

    def __init__(self, **kwargs):
        pass

    def list_networks(self, **search_opts):
        networks = [copy.deepcopy(r) for r in FAKE_NETWORKS["networks"]
                    if all(r.get(a) == search_opts[a] for a in search_opts)]
        return {"networks": networks}

    def show_subnet(self, subnet_id):
        for subnet in FAKE_SUBNETS:
            if subnet["subnet"]["id"] == subnet_id:
                return subnet
        return None

    def list_subnets(self, retrieve_all=True, **_params):
        subnets = [copy.deepcopy(s) for s in FAKE_SUBNETS
                   if all(s.get(a) == _params[a] for a in _params)]
        return {"subnets": subnets}

    def create_network(self, body):
        return {u'network':
                {u'status': u'ACTIVE',
                 u'subnets': [],
                 u'name': body["network"]["name"],
                 u'provider:physical_network': None,
                 u'admin_state_up': True,
                 u'tenant_id': fake_request.PROJECT_ID,
                 u'provider:network_type': u'local',
                 u'router:external': False,
                 u'shared': False,
                 u'id': u'f1b1bc03-9955-4fd8-bdf9-d2ec7d2777e7',
                 u'provider:segmentation_id': None}}

    def create_subnet(self, body):
        return {u'subnet':
                {u'name': u'',
                 u'enable_dhcp': True,
                 u'network_id': u'f1b1bc03-9955-4fd8-bdf9-d2ec7d2777e7',
                 u'tenant_id': fake_request.PROJECT_ID,
                 u'dns_nameservers': [],
                 u'allocation_pools': [
                                       {u'start': u'10.100.0.2',
                                        u'end': u'10.100.0.254'}
                                       ],
                 u'host_routes': [],
                 u'ip_version': 4,
                 u'gateway_ip': u'10.100.0.1',
                 u'cidr': u'10.100.0.0/24',
                 u'id': u'9d550616-b294-4897-9eb4-7f998aa7a74e'}}

    def delete_network(self, network_id):
        pass

    def list_routers(self, retrieve_all=True, **_params):
        routers = [copy.deepcopy(r) for r in FAKE_ROUTERS
                   if all(r.get(a) == _params[a] for a in _params)]
        return {"routers": routers}

    def show_router(self, router):
        return {"router": copy.deepcopy(next(r for r in FAKE_ROUTERS
                                             if r["id"] == router))}

    def create_router(self, body=None):
        return {"router": {"id": str(uuid.uuid4())}}

    def update_router(self, router, body=None):
        pass

    def add_gateway_router(self, router, body=None):
        routers = self.list_routers(id=router)["routers"]
        if len(routers) == 1:
            return {"router": routers[0]}

    def add_interface_router(self, router, body=None):
        pass

    def remove_gateway_router(self, router):
        pass

    def list_ports(self, *args, **kwargs):
        ports = [p for p in FAKE_PORTS
                 if all(p.get(a) == kwargs[a] for a in kwargs)]
        return {"ports": ports}

    def list_floatingips(self, tenant_id):
        return FAKE_ADDRESSES

    def create_floatingip(self, body=None):
        return {"floatingip": {"id": str(uuid.uuid4()),
                               "floating_ip_address": "10.20.30.40"}}

    def delete_floatingip(self, floatingip):
        pass

    def show_quota(self, tenant_id, **_params):
        return FAKE_QUOTAS

    def list_security_groups(self, retrieve_all=True, **_params):
        return FAKE_SECURITY_GROUPS
