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
import string

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import network_api
from gceapi.api import operation_util
from gceapi.api import utils
from gceapi import exception
from gceapi.i18n import _


ALL_IP_CIDR = "0.0.0.0/0"


class API(base_api.API):
    """GCE Address API - neutron implementation."""

    KIND = "route"
    PERSISTENT_ATTRIBUTES = ["id", "creationTimestamp", "description",
                             "is_default"]
    TRANS_TABLE = string.maketrans("./", "--")

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        network_api.API()._register_callback(
            base_api._callback_reasons.post_add,
            self._create_network_router)
        network_api.API()._register_callback(
            base_api._callback_reasons.check_delete,
            self._check_delete_network)
        network_api.API()._register_callback(
            base_api._callback_reasons.pre_delete,
            self._delete_network_router)

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, name, scope=None):
        routes, dummy = self._sync_routes(context)
        return routes[name]

    def get_items(self, context, scope=None):
        routes, dummy = self._sync_routes(context)
        return routes.values()

    def delete_item(self, context, name, scope=None):
        routes, aliased_routes = self._sync_routes(context)
        route = routes[name]
        if route.get("nexthop") is None:
            raise exception.InvalidInput(
                    _("The local route cannot be deleted."))
        destination = route["destination"]
        nexthop = route["nexthop"]
        # NOTE(ft): delete OS route only if it doesn't have aliases
        # at the moment
        client = clients.neutron(context)
        operation_util.start_operation(context)
        if self._get_route_key(route) not in aliased_routes:
            dummy, router = self._get_network_objects(client,
                                                      route["network"])
            if "external_gateway_info" in route:
                client.remove_gateway_router(router["id"])
            else:
                routes = [r for r in router["routes"]
                          if (destination != r["destination"] or
                              nexthop != r["nexthop"])]
                client.update_router(
                        router["id"],
                        {"router": {"routes": routes, }, })
        self._delete_db_item(context, route)

    def add_item(self, context, name, body, scope=None):
        routes, dummy = self._sync_routes(context)
        if name in routes:
            raise exception.InvalidInput(
                    _("The resource '%s' already exists.") % name)

        # NOTE(ft): check network is plugged to router
        network_name = utils._extract_name_from_url(body["network"])
        network = network_api.API().get_item(context, network_name)

        nexthop = body.get("nextHopGateway")
        if (nexthop is not None and
                (utils._extract_name_from_url(nexthop) ==
                 "default-internet-gateway") and
                # NOTE(ft): OS doesn't support IP mask for external gateway
                body.get("destRange") == ALL_IP_CIDR):
            operation_util.start_operation(context)
            return self._create_internet_route(context, network, body)

        nexthop = body.get("nextHopIp")
        if nexthop is not None:
            operation_util.start_operation(context)
            return self._create_custom_route(context, network, body)

        raise exception.InvalidInput(_("Unsupported route."))

    def _create_internet_route(self, context, network, body):
        client = clients.neutron(context)
        port, router = self._get_network_objects(client, network)
        public_network_id = network_api.API().get_public_network_id(context)
        external_gateway_info = {"network_id": public_network_id}
        router = client.add_gateway_router(
                router["id"],
                external_gateway_info)["router"]
        # TODO(alexey-mr): ?admin needed - router_gateway ports haven't tenant
        ports = client.list_ports(device_id=router["id"],
                                  device_owner="network:router_gateway")
        gateway_port = ports["ports"][0]
        route = self._add_gce_route(context, network, port, body,
                                   is_default=False,
                                   destination=gateway_port["id"],
                                   nexthop=ALL_IP_CIDR)
        route["network"] = network
        route["port"] = port
        route["external_gateway_info"] = external_gateway_info
        return route

    def _create_custom_route(self, context, network, body):
        client = clients.neutron(context)
        port, router = self._get_network_objects(client, network)
        destination = body.get("destRange")
        nexthop = body.get("nextHopIp")
        routes = router["routes"]
        if all(r["destination"] != destination or r["nexthop"] != nexthop
               for r in routes):
            routes.append({
                    "destination": destination,
                    "nexthop": nexthop,
                })
            client.update_router(
                    router["id"],
                    {"router": {"routes": router["routes"], }, })
        route = self._add_gce_route(context, network, port, body,
                                   is_default=False, destination=destination,
                                   nexthop=nexthop)
        route["network"] = network
        route["port"] = port
        return route

    def _sync_routes(self, context):
        os_routes = self._get_os_routes(context)
        gce_routes = self._get_gce_routes(context)
        aliased_routes = {}
        routes = {}
        for (key, os_route) in os_routes.items():
            gce_route_list = gce_routes.pop(key, None)
            if gce_route_list is None:
                continue
            for gce_route in gce_route_list:
                routes[gce_route["name"]] = dict(os_route, **dict(gce_route))
            os_routes.pop(key)
            if len(gce_route_list) > 1:
                aliased_routes[key] = gce_route_list

        # NOTE(ft): add new named routes
        for os_route in os_routes.itervalues():
            network = os_route["network"]
            port = os_route["port"]
            route = self._add_gce_route(context, network, port, os_route,
                                       is_default=True,
                                       creationTimestamp="")
            os_route.update(route)
            routes[os_route["name"]] = os_route

        # NOTE(ft): delete obsolete named routes
        for gce_route_list in gce_routes.itervalues():
            for gce_route in gce_route_list:
                self._delete_db_item(context, gce_route)
        return (routes, aliased_routes)

    def _get_gce_routes(self, context):
        gce_routes = self._get_db_items(context)
        gce_routes_dict = {}
        for route in gce_routes:
            route = self._unpack_route_from_db_format(route)
            key = self._get_route_key(route)
            val_array = gce_routes_dict.get(key)
            if val_array is None:
                gce_routes_dict[key] = [route]
            else:
                val_array.append(route)
        return gce_routes_dict

    def _get_route_key(self, route):
        if route["port_id"] is None:
            return route["network_id"]
        else:
            return (route["network_id"] + route["port_id"] +
                    route["destination"] + route["nexthop"])

    def _get_os_routes(self, context):
        client = clients.neutron(context)
        routers = client.list_routers(tenant_id=context.project_id)["routers"]
        routers = dict((r["id"], r) for r in routers)
        ports = client.list_ports(
                tenant_id=context.project_id,
                device_owner="network:router_interface")["ports"]
        ports = dict((p["network_id"], p) for p in ports)
        gateway_ports = client.list_ports(
                device_owner="network:router_gateway")["ports"]
        gateway_ports = dict((p["device_id"], p) for p in gateway_ports)
        routes = {}
        networks = network_api.API().get_items(context)
        for network in networks:
            # NOTE(ft): append local route
            network_id = network["id"]
            routes[network_id] = self._init_local_route(network)

            port = ports.get(network_id)
            if port is None:
                continue
            router = routers.get(port["device_id"])
            if router is None:
                continue
            key_prefix = network_id + port["id"]

            # NOTE(ft): append internet route
            external_gateway_info = router.get("external_gateway_info")
            gateway_port = gateway_ports.get(router["id"])
            if (external_gateway_info is not None and
                    gateway_port is not None):
                key = key_prefix + ALL_IP_CIDR + gateway_port["id"]
                routes[key] = self._init_internet_route(
                        network, port, gateway_port["id"],
                        external_gateway_info)

            # NOTE(ft): append other routes
            for route in router["routes"]:
                destination = route["destination"]
                nexthop = route["nexthop"]
                key = key_prefix + destination + nexthop
                routes[key] = self._init_custom_route(
                        network, port, destination, nexthop)
        return routes

    def _get_network_objects(self, client, network):
        subnet_id = network.get("subnet_id")
        if subnet_id is None:
            raise exception.PortNotFound(_("Network has no router."))
        ports = client.list_ports(
                network_id=network["id"],
                device_owner="network:router_interface")["ports"]
        port = next((p for p in ports
                     if any(fip["subnet_id"] == subnet_id
                            for fip in p["fixed_ips"])), None)
        if port is None:
            raise exception.PortNotFound(_("Network has no router."))
        router = client.show_router(port["device_id"])["router"]
        return (port, router)

    def _create_network_router(self, context, network, subnet_id):
        public_network_id = network_api.API().get_public_network_id(context)
        client = clients.neutron(context)
        router = client.create_router(body={"router": {
            "name": network["name"],
            "admin_state_up": True,
            "external_gateway_info": {"network_id": public_network_id},
        }})["router"]
        client.add_interface_router(router["id"], {"subnet_id": subnet_id})

    def _check_delete_network(self, context, network):
        network_id = network["id"]
        # NOTE(ft): check non default routes not longer exists
        # must be done for internet routes
        routes, dummy = self._sync_routes(context)
        for route in routes.itervalues():
            if (route["network_id"] == network_id and
                    not route["is_default"]):
                raise exception.InvalidInput(_("Network contains routes"))
        # NOTE(ft): check invisible routes not longer exists
        # must be done for routes on non default subnet and other non GCE stuff
        client = clients.neutron(context)
        checked_routers = set()
        subnets = client.list_subnets(network_id=network_id)["subnets"]
        cidrs = [netaddr.IPNetwork(subnet["cidr"]) for subnet in subnets]
        ports = client.list_ports(
                network_id=network["id"],
                device_owner="network:router_interface")["ports"]
        for port in ports:
            if port["device_id"] in checked_routers:
                continue
            checked_routers.add(port["device_id"])
            router = client.show_router(port["device_id"])["router"]
            for route in router["routes"]:
                nexthop = netaddr.IPAddress(route["nexthop"])
                if any(nexthop in cidr for cidr in cidrs):
                    raise exception.InvalidInput(_("Network contains routes"))
        # TODO(ft): here is the good place to create default routes in DB
        # now thew will be created on next 'route' request,
        # but 'creationTimestamp' will be absent

    def _delete_network_router(self, context, network):
        client = clients.neutron(context)
        ports = client.list_ports(
                network_id=network["id"],
                device_owner="network:router_interface")["ports"]
        router_ids = set()
        for port in ports:
            if port["device_owner"] == "network:router_interface":
                router_ids.add(port["device_id"])
                client.remove_interface_router(port["device_id"],
                                               {"port_id": port["id"]})
        # NOTE(ft): leave routers if network is plugged to more than one route
        # because it's look like some non GCE settings, so we don't want
        # to decide whether we can delete router or not
        if len(router_ids) != 1:
            return
        router = router_ids.pop()
        # NOTE(ft): leave router if other subnets are plugged to it
        ports = client.list_ports(
                device_id=router,
                device_owner="network:router_interface")["ports"]
        if len(ports) == 0:
            client.delete_router(router)
        # TODO(ft): here is the good place to purge DB from routes

    def _add_gce_route(self, context, network, port, route, **kwargs):
        db_route = {}
        for key in self.PERSISTENT_ATTRIBUTES:
            value = route.get(key)
            if value is None:
                value = kwargs.get(key)
            if value is not None or key in kwargs:
                db_route[key] = value

        def get_from_dicts(key, dict1, dict2, default=None):
            value = dict1.get(key)
            if value is None:
                value = dict2.get(key)
            return value if value is not None else default

        route_id = "//".join([network["id"],
                              port["id"] if port is not None else "",
                              get_from_dicts("destination", route, kwargs),
                              get_from_dicts("nexthop", route, kwargs, ""),
                              get_from_dicts("name", route, kwargs)])
        db_route["id"] = route_id
        db_route = self._add_db_item(context, db_route)
        return self._unpack_route_from_db_format(db_route)

    def _unpack_route_from_db_format(self, route):
        parts = route["id"].split("//")
        route["network_id"] = parts[0]
        route["port_id"] = parts[1] if parts[1] != "" else None
        route["destination"] = parts[2]
        route["nexthop"] = parts[3] if parts[3] != "" else None
        route["name"] = parts[4]
        return route

    def _init_local_route(self, network):
        return {
            "id": None,
            "name": "default-route-%s-local" % network["id"],
            "description": "Default route to the virtual network.",
            "network": network,
            "port": None,
            "destination": network.get("IPv4Range", ""),
            "nexthop": None,
            "is_default": True,
        }

    def _init_internet_route(self, network, port, nexthop, gateway_info):
        return {
            "id": None,
            "name": "default-route-%s-internet" % network["id"],
            "description": "Default route to the Internet.",
            "network": network,
            "port": port,
            "destination": ALL_IP_CIDR,
            "nexthop": nexthop,
            "is_default": True,
            "external_gateway_info": gateway_info,
        }

    def _init_custom_route(self, network, port, destination, nexthop):
        name = ("custom-route-%(nw)s-dst-%(dst)s-gw-%(nh)s" %
                {
                    "nw": network["id"],
                    "dst": destination,
                    "nh": nexthop,
                })
        name = str(name).translate(self.TRANS_TABLE)
        return {
            "id": None,
            "name": name,
            "network": network,
            "port": port,
            "destination": destination,
            "nexthop": nexthop,
            "is_default": False,
        }
