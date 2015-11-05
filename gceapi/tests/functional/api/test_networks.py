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

from gceapi.tests.functional import test_base


CREATE_NETWORK_TEMPLATE = {
    "name": "${name}",
    "IPv4Range": "10.240.0.0/16",
    "description": "testing network ${name}",
    "gatewayIPv4": "10.240.0.1"
}


def _prepare_network_create_parameters(**kwargs):
    return test_base.insert_json_parameters(CREATE_NETWORK_TEMPLATE, **kwargs)


class TestNetworksBase(test_base.GCETestCase):
    @property
    def networks(self):
        res = self.api.compute.networks()
        self.assertIsNotNone(
            res,
            'Null networks object, api is not built properly')
        return res

    def setUp(self):
        super(TestNetworksBase, self).setUp()
        self._network_name = self.getUniqueString('testnet')

    def _create_network(self):
        cfg = self.cfg
        project_id = cfg.project_id
        network = self._network_name
        kw = {
            'name': network,
        }
        config = _prepare_network_create_parameters(**kw)
        self.trace('Crete network with options {}'.format(config))
        request = self.networks.insert(
            project=project_id,
            body=config)
        result = self._execute_async_request(request, project_id)
        self.api.validate_schema(value=result, schema_name='Operation')
        return result

    def _delete_network(self):
        cfg = self.cfg
        project_id = cfg.project_id
        network = self._network_name
        self.trace('Delete network: project_id={} network={}'.
                   format(project_id, network))
        request = self.networks.delete(
            project=project_id,
            network=network)
        result = self._execute_async_request(request, project_id)
        self.api.validate_schema(value=result, schema_name='Operation')
        return result

    def _list_networks(self):
        project_id = self.cfg.project_id
        self.trace('List networks: project_id={}'.format(project_id))
        request = self.networks.list(project=project_id)
        self._trace_request(request)
        result = request.execute()
        self.trace('Networks: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='NetworkList')
        self.assertFind(self._network_name, result)
        return result

    def _get_network(self):
        project_id = self.cfg.project_id
        network = self._network_name
        self.trace('Get network: project_id={} network={}'.
                   format(project_id, network))
        request = self.networks.get(
            project=project_id,
            network=network)
        result = request.execute()
        self.trace('Network: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Network')
        return result

    def _create(self):
        self._create_network()

    def _read(self):
        self._get_network()
        self._list_networks()

    def _update(self):
        # TODO(alexey-mr): to impl simple update cases
        pass

    def _delete(self):
        self._delete_network()


class TestNeutronNetworksCRUD(TestNetworksBase):
    def setUp(self):
        if self.cfg.networking == 'nova-network':
            self.skipTest('Skip network because of nova-network')
            return
        super(TestNeutronNetworksCRUD, self).setUp()

    def test_crud(self):
        self._create()
        self._read()
        self._update()
        self._delete()


class TestNovaNetworksCRUD(TestNetworksBase):
    def setUp(self):
        if self.cfg.networking != 'nova-network':
            self.skipTest('Skip network because of not nova-network')
            return
        super(TestNovaNetworksCRUD, self).setUp()
        # override name of network
        # nova-networking expects that default network is created
        self._network_name = 'default'

    def test_crud(self):
        self._read()
