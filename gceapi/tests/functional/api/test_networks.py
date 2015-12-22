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


NETWORK_URL_TEMPLATE = 'global/networks/{}'
DEFAULT_NETWORK_NAME = 'default'
DEFAULT_NETWORK_URL = NETWORK_URL_TEMPLATE.format(DEFAULT_NETWORK_NAME)
DEFAULT_NETWORK_IP_RANGE = u'10.240.0.0/16'
DEFAULT_NETWORK_GATEWAY = u'10.240.0.1'


def ip_to_re_pattern(ip):
    return test_base.string_to_re_pattern(ip)


class TestNetworksBase(test_base.GCETestCase):
    @property
    def networks(self):
        res = self.api.compute.networks()
        self.assertIsNotNone(
            res,
            'Null networks object, api is not built properly')
        return res

    def _create_network(self, options):
        project_id = self.cfg.project_id
        self.trace('Create network with options {}'.format(options))
        request = self.networks.insert(
            project=project_id,
            body=options)
        self._add_cleanup(self._delete_network, options['name'])
        self._execute_async_request(request, project_id)

    def _delete_network(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        self.trace('Delete network: project_id={} network={}'.
                   format(project_id, name))
        request = self.networks.delete(
            project=project_id,
            network=name)
        self._execute_async_request(request, project_id)
        self._remove_cleanup(self._delete_network, name)

    def _list_networks(self, filter=None):
        project_id = self.cfg.project_id
        self.trace('List networks: project_id={}'.format(project_id))
        request = self.networks.list(project=project_id, filter=filter)
        self.trace_request(request)
        result = request.execute()
        self.trace('Networks: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='NetworkList')
        return result

    def _get_network(self, name):
        project_id = self.cfg.project_id
        self.trace('Get network: project_id={} network={}'.
                   format(project_id, name))
        request = self.networks.get(
            project=project_id,
            network=name)
        result = request.execute()
        self.trace('Network: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Network')
        return result

    def _get_expected_network(self, options):
        network = copy.deepcopy(options)
        network.setdefault('kind', u'compute#network')
        self_link = NETWORK_URL_TEMPLATE.format(network['name'])
        network.setdefault('selfLink', self.api.get_project_url(self_link))
        ip_range = network.get('IPv4Range', DEFAULT_NETWORK_IP_RANGE)
        network['IPv4Range'] = ip_to_re_pattern(ip_range)
        gateway = network.get('gatewayIPv4', DEFAULT_NETWORK_GATEWAY)
        network['gatewayIPv4'] = ip_to_re_pattern(gateway)
        return network

    def _ensure_network_created(self, options):
        network = self._get_network(options['name'])
        expected_network = self._get_expected_network(options)
        self.assertObject(expected_network, network)
        return network

    def _create_and_validate_network(self, options):
        self._create_network(options)
        return self._ensure_network_created(options)


class TestNetworks(TestNetworksBase):
    def test_get_default_network(self):
        name = DEFAULT_NETWORK_NAME
        network = self._get_network(name)
        options = {
            'name': name
        }
        expected = self._get_expected_network(options)
        self.assertObject(expected, network)

    def test_list_default_network(self):
        name = DEFAULT_NETWORK_NAME
        result = self._list_networks()
        result = self.assertFind(name, result)
        options = {
            'name': name
        }
        expected = self._get_expected_network(options)
        self.assertObject(expected, result)

    def test_list_default_network_by_filter(self):
        name = DEFAULT_NETWORK_NAME
        result = self._list_networks(filter='name eq {}'.format(name))
        result = self.assertFind(name, result)
        options = {
            'name': name
        }
        expected = self._get_expected_network(options)
        self.assertObject(expected, result)

    def test_create_network_default(self):
        if self.is_nova_network:
            self.skipTest('Skip network because of nova-network')
            return
        name = self._rand_name('testnetwork')
        options = {
            'name': name,
        }
        self._create_and_validate_network(options)
        self._delete_network(name)

    def test_create_network_with_ip_range(self):
        if self.is_nova_network:
            self.skipTest('Skip because of nova-network cannot create network')
            return
        name = self._rand_name('testnetwork')
        options = {
            'name': name,
            'IPv4Range': '10.241.0.0/16',
        }
        self._create_network(options)
        options['gatewayIPv4'] = '10.241.0.1'
        self._ensure_network_created(options)
        self._delete_network(name)

    def test_create_network_with_gateway(self):
        if self.is_nova_network:
            self.skipTest('Skip network because of nova-network')
            return
        name = self._rand_name('testnetwork')
        options = {
            'name': name,
            'IPv4Range': '10.242.0.0/16',
            'gatewayIPv4': '10.242.0.1'
        }
        self._create_and_validate_network(options)
        self._delete_network(name)

    def test_list_networks_by_filter_name(self):
        if self.is_nova_network:
            self.skipTest('Skip network because of nova-network')
            return
        names = [self._rand_name('testnetwork') for _ in range(0, 3)]
        networks = dict()
        for name in names:
            options = {
                'name': name,
            }
            networks[name] = self._create_and_validate_network(options)
        for name in names:
            result = self._list_networks(filter='name eq {}'.format(name))
            network = self.assertFind(name, result)
            self.assertObject(networks[name], network)
        for name in names:
            self._delete_network(name)
