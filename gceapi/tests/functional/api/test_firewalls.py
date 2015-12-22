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

from gceapi.tests.functional.api import test_networks


class TestFirewallBase(test_networks.TestNetworksBase):
    @property
    def firewalls(self):
        res = self.api.compute.firewalls()
        self.assertIsNotNone(
            res,
            'Null firewalls object, api is not built properly')
        return res

    def _create_firewall(self, options):
        project_id = self.cfg.project_id
        self.trace('Create firewall with options {}'.format(options))
        request = self.firewalls.insert(
            project=project_id,
            body=options)
        self._add_cleanup(self._delete_firewall, options['name'])
        self._execute_async_request(request, project_id)

    def _delete_firewall(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        self.trace('Delete firewall: project_id={} firewall={}'.
                   format(project_id, name))
        request = self.firewalls.delete(
            project=project_id,
            firewall=name)
        self._execute_async_request(request, project_id)
        self._remove_cleanup(self._delete_firewall, name)

    def _list_firewalls(self, filter=None):
        project_id = self.cfg.project_id
        self.trace('List firewalls: project_id={}'.format(project_id))
        request = self.firewalls.list(project=project_id, filter=filter)
        self.trace_request(request)
        result = request.execute()
        self.trace('Firewalls: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='FirewallList')
        return result

    def _get_firewall(self, name):
        project_id = self.cfg.project_id
        self.trace('Get firewall: project_id={} firewall={}'.
                   format(project_id, name))
        request = self.firewalls.get(
            project=project_id,
            firewall=name)
        result = request.execute()
        self.trace('Firewall: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Firewall')
        return result

    def _get_expected_firewall(self, options):
        firewall = copy.deepcopy(options)
        firewall.setdefault('kind', u'compute#firewall')
        self_link = 'global/firewalls/{}'.format(firewall['name'])
        firewall.setdefault('selfLink', self.api.get_project_url(self_link))
        # just to check on exist
        firewall.setdefault('allowed', [])
        # TODO(alexey-mr): OS GCE default firewall doesn't provide network
        # firewall.setdefault('network', '.*')
        return firewall

    def _ensure_firewall_created(self, options):
        result = self._get_firewall(options['name'])
        expected = self._get_expected_firewall(options)
        self.assertObject(expected, result)
        return result

    def _create_firewall_and_validate(self, options):
        self._create_firewall(options)
        result = self._get_firewall(options['name'])
        expected = self._get_expected_firewall(options)
        self.assertObject(expected, result)
        return expected


class TestFirewalls(TestFirewallBase):
    def test_list_default_firewalls(self):
        result = self._list_firewalls()
        for firewall in result['items']:
            options = {
                'name': firewall['name']
            }
            expected = self._get_expected_firewall(options)
            self.assertObject(expected, firewall)

    def test_create_delete_firewall_ip_range_tcp_port(self):
        name = self._rand_name('testfirewall')
        options = {
            'name': name,
            'allowed': [
                {
                    'IPProtocol': 'tcp',
                    'ports': ['44444']
                }
            ],
            'sourceRanges': ['10.240.0.0/16']
        }
        self._create_firewall_and_validate(options)
        self._delete_firewall(name)

    def test_create_delete_firewall_source_tag_tcp_port_range(self):
        if not self.full_compatibility:
            self.skipTest('Skip because of OS GCE does not support tags')
            return
        name = self._rand_name('testfirewall')
        options = {
            'name': name,
            'allowed': [
                {
                    'IPProtocol': 'tcp',
                    'ports': ['50000-55000']
                }
            ],
            'sourceTags': ['no-ip']
        }
        self._create_firewall_and_validate(options)
        self._delete_firewall(name)

    def test_create_delete_firewall_target_tag_tcp_empty_ports(self):
        if not self.full_compatibility:
            self.skipTest('Skip because of OS GCE does not support tags')
            return
        name = self._rand_name('testfirewall')
        options = {
            'name': name,
            'allowed': [
                {
                    'IPProtocol': 'tcp'
                }
            ],
            'sourceTags': ['src-no-ip'],
            'targetTags': ['trg-no-ip']
        }
        self._create_firewall_and_validate(options)
        self._delete_firewall(name)

    def _prepare_network(self):
        name = self._rand_name('testnetwork')
        options = {
            'name': name,
            'IPv4Range': '10.241.0.0/16',
        }
        self._create_network(options)
        options['gatewayIPv4'] = '10.241.0.1'
        return self._ensure_network_created(options)

    def test_create_delete_firewall_custom_network(self):
        if self.is_nova_network:
            self.skipTest('Skip because of nova-network cannot create network')
            return
        network = self._prepare_network()
        name = self._rand_name('testfirewall')
        options = {
            'name': name,
            'allowed': [
                {
                    'IPProtocol': 'udp',
                    'ports': ['30000', '40000', '50000-51000']
                },
                {
                    'IPProtocol': 'icmp'
                }
            ],
            'sourceRanges': [network['IPv4Range']],
            'network': network['selfLink']
        }
        self._create_firewall_and_validate(options)
        self._delete_firewall(name)
        self._delete_network(network['name'])
