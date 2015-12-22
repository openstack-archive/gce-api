# Copyright 2015 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

import copy

from gceapi.tests.functional import test_base

from gceapi.tests.functional.api import test_instances
from gceapi.tests.functional.api import test_networks


DEFAULT_NETWORK_URL = test_networks.DEFAULT_NETWORK_URL
DEFAULT_NETWORK_GATEWAY = test_networks.DEFAULT_NETWORK_GATEWAY
DEFAULT_GLOBAL_INTERNET_GATEWAY = u'global/gateways/default-internet-gateway'
DEFAULT_ROUTE_PRIORITY = '1000'


class TestRouteBase(test_base.GCETestCase):
    @property
    def routes(self):
        res = self.api.compute.routes()
        self.assertIsNotNone(
            res,
            'Null routes object, api is not built properly')
        return res

    def _create_route(self, options):
        project_id = self.cfg.project_id
        self.trace('Create route with options {}'.format(options))
        request = self.routes.insert(
            project=project_id,
            body=options)
        self._add_cleanup(self._delete_route, options['name'])
        self._execute_async_request(request, project_id)

    def _delete_route(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        self.trace('Delete route: project_id={} route={}'.
                   format(project_id, name))
        request = self.routes.delete(
            project=project_id,
            route=name)
        self._execute_async_request(request, project_id)
        self._remove_cleanup(self._delete_route, name)

    def _list_routes(self, filter=None):
        project_id = self.cfg.project_id
        self.trace('List routes: project_id={}'.format(project_id))
        request = self.routes.list(project=project_id, filter=filter)
        self.trace_request(request)
        result = request.execute()
        self.trace('Routes: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='RouteList')
        return result

    def _get_route(self, name):
        project_id = self.cfg.project_id
        self.trace('Get route: project_id={} route={}'.
                   format(project_id, name))
        request = self.routes.get(
            project=project_id,
            route=name)
        result = request.execute()
        self.trace('Route: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Route')
        return result

    def _get_expected_route(self, options):
        route = copy.deepcopy(options)
        route.setdefault('kind', u'compute#route')
        self_link = 'global/routes/{}'.format(route['name'])
        route.setdefault('selfLink', self.api.get_project_url(self_link))
        route.setdefault('destRange', '')
        route.setdefault('priority', '1000')
        # convert to full url if needed
        network_url = route.get('network', DEFAULT_NETWORK_URL)
        route['network'] = self.api.get_project_url(network_url)
        next_gateway = route.get('nextHopGateway')
        if next_gateway:
            # convert to full url if needed
            next_gateway = self.api.get_project_url(next_gateway)
            route['nextHopGateway'] = next_gateway
        # May not be provided in default GCE routes, so do not check
        #   by default
        # route.setdefault('nextHopNetwork', '')
        # route.setdefault('nextHopInstance', '')
        # route.setdefault('nextHopIp', '')
        # route.setdefault('nextHopVpnTunnel', '')
        # route.setdefault('tags', [])
        return route

    def _ensure_route_created(self, options):
        result = self._get_route(options['name'])
        expected = self._get_expected_route(options)
        self.assertObject(expected, result)
        return result

    def _create_route_and_validate(self, options):
        self._create_route(options)
        result = self._get_route(options['name'])
        expected = self._get_expected_route(options)
        self.assertObject(expected, result)
        return expected


class TestRoutes(TestRouteBase,
                 test_networks.TestNetworksBase,
                 test_instances.TestInstancesBase):
    @property
    def skip_if_nova_network(self):
        if super(TestRoutes, self).is_nova_network:
            self.skipTest('Skip network because of nova-network cant create'
                          ' new networks')
            return True
        return False

    def test_list_default_routes(self):
        if self.skip_if_nova_network:
            return
        result = self._list_routes()
        for route in result['items']:
            options = {
                'name': route['name']
            }
            expected = self._get_expected_route(options)
            self.assertObject(expected, route)

    def test_create_delete_route_default_network_next_gateway(self):
        if not self.full_compatibility:
            self.skipTest('OS does not support IP mask for external gateway')
            return
        if self.skip_if_nova_network:
            return
        name = self._rand_name('testroute')
        network_url = self.api.get_project_url(DEFAULT_NETWORK_URL)
        options = {
            'name': name,
            'priority': DEFAULT_ROUTE_PRIORITY,
            'network': DEFAULT_NETWORK_URL,
            'destRange': u'10.0.0.0/8',
            'nextHopGateway': DEFAULT_GLOBAL_INTERNET_GATEWAY
        }
        self._create_route_and_validate(options)
        self._delete_route(name)

    def test_create_delete_route_default_network_next_ip(self):
        if self.skip_if_nova_network:
            return
        name = self._rand_name('testroute')
        network_url = self.api.get_project_url(DEFAULT_NETWORK_URL)
        options = {
            'name': name,
            'priority': DEFAULT_ROUTE_PRIORITY,
            'network': DEFAULT_NETWORK_URL,
            'destRange': u'10.0.0.0/8',
            'nextHopIp': u'10.240.0.10'
        }
        self._create_route_and_validate(options)
        self._delete_route(name)

    def _prepare_instance(self):
        name = self._rand_name('testinstance')
        options = self._get_create_instance_from_image_options(name)
        options['canIpForward'] = True
        self._create_instance(options)
        return self._ensure_instance_created(options)

    def test_create_delete_route_default_network_next_instance(self):
        if not self.full_compatibility:
            self.skipTest('OS GCE does not support nextHopInstance')
            return
        if self.skip_if_nova_network:
            return
        instance = self._prepare_instance()
        name = self._rand_name('testroute')
        options = {
            'name': name,
            'priority': DEFAULT_ROUTE_PRIORITY,
            'network': DEFAULT_NETWORK_URL,
            'destRange': u'10.0.0.0/8',
            'nextHopInstance': instance['selfLink']
        }
        self._create_route_and_validate(options)
        self._delete_route(name)
        self._delete_instance(instance['name'])

    def _prepare_network(self):
        name = self._rand_name('testnetwork')
        options = {
            'name': name,
            'IPv4Range': '10.241.0.0/16',
            'gatewayIPv4': '10.241.0.1'
        }
        return self._create_and_validate_network(options)

    def test_create_delete_route_network_next_ip(self):
        if self.skip_if_nova_network:
            return
        network = self._prepare_network()
        name = self._rand_name('testroute')
        options = {
            'name': name,
            'priority': DEFAULT_ROUTE_PRIORITY,
            'network': network['selfLink'],
            'destRange': u'10.0.0.0/8',
            'nextHopIp': u'10.241.0.10'
        }
        self._create_route_and_validate(options)
        self._delete_route(name)
        self._delete_network(network['name'])
