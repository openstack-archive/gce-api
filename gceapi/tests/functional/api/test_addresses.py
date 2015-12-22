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


IPV4_PATTERN = ('^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                '(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')


class TestAddressesBase(test_base.GCETestCase):
    @property
    def addresses(self):
        res = self.api.compute.addresses()
        self.assertIsNotNone(
            res,
            'Null addresses object, api is not built properly')
        return res

    def _create_address(self, options):
        cfg = self.cfg
        project_id = cfg.project_id
        region = cfg.region
        self.trace('Create address with options {}'.format(options))
        request = self.addresses.insert(
            project=project_id,
            region=region,
            body=options)
        self._add_cleanup(self._delete_address, options['name'])
        self._execute_async_request(request, project_id, region=region)

    def _delete_address(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        region = cfg.region
        self.trace('Delete address: project_id={} region={} name={}'.
                   format(project_id, region, name))
        request = self.addresses.delete(
            project=project_id,
            region=region,
            address=name)
        self._execute_async_request(request, project_id, region=region)
        self._remove_cleanup(self._delete_address, name)

    def _list_addresses(self, filter=None):
        cfg = self.cfg
        project_id = cfg.project_id
        region = cfg.region
        self.trace('List addresses: project_id={} region={}'.
                   format(project_id, region))
        request = self.addresses.list(
            project=project_id,
            region=region,
            filter=filter)
        result = request.execute()
        self.trace('Addresses: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='AddressList')
        return result

    def _get_address(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        region = cfg.region
        self.trace('Get address: project_id={} region={} name={}'.
                   format(project_id, region, name))
        request = self.addresses.get(
            project=project_id,
            region=region,
            address=name)
        result = request.execute()
        self.trace('Addresses: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Address')
        return result

    def _get_expected_address(self, options):
        address = copy.deepcopy(options)
        address['kind'] = u'compute#address'
        if 'status' not in options:
            address['status'] = u'RESERVED'
        if 'selfLink' not in options:
            address_link = 'addresses/{}'.format(address['name'])
            address['selfLink'] = self.api.get_region_url(address_link)
        if 'region' not in options:
            address['region'] = self.api.get_region_url()
        if 'address' not in options:
            address['address'] = IPV4_PATTERN
        if 'id' not in options:
            address['id'] = '[0-9]{1,32}'
        return address

    def _ensure_address_created(self, options):
        name = options['name']
        address = self._get_address(name)
        expected_address = self._get_expected_address(options)
        self.assertObject(expected_address, address)
        return address


class TestAddressess(TestAddressesBase):
    @property
    def addresses(self):
        res = self.api.compute.addresses()
        self.assertIsNotNone(
            res,
            'Null addresses object, api is not built properly')
        return res

    def setUp(self):
        super(TestAddressess, self).setUp()

    def test_create_delete_address(self):
        name = self._rand_name('testaddr')
        options = {
            'name': name
        }
        self._create_address(options)
        self._ensure_address_created(options)
        self._delete_address(name)

    def test_list_addresses(self):
        name = self._rand_name('testaddr')
        options = {
            'name': name
        }
        self._create_address(options)
        address = self._ensure_address_created(options)
        result = self._list_addresses()
        result = self.assertFind(name, result)
        self.assertObject(address, result)
        self._delete_address(name)

    def test_list_addresses_by_filter_name(self):
        names = [self._rand_name('testaddr') for _ in range(0, 3)]
        # prepare resources
        addresses = dict()
        for name in names:
            options = {
                'name': name
            }
            self._create_address(options)
            addresses[name] = self._ensure_address_created(options)
        # do list by filter test
        for name in names:
            result = self._list_addresses(filter='name eq {}'.format(name))
            self.assertEqual(1, len(result['items']))
            self.assertObject(addresses[name], result['items'][0])
        # delete resources
        for name in names:
            self._delete_address(name)
