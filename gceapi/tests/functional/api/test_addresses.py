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


CREATE_ADDRESS_TEMPLATE = {
    "name": "${name}",
}


def _prepare_address_create_parameters(**kwargs):
    return test_base.insert_json_parameters(CREATE_ADDRESS_TEMPLATE, **kwargs)


class TestAddressesBase(test_base.GCETestCase):
    @property
    def addresses(self):
        res = self.api.compute.addresses()
        self.assertIsNotNone(
            res,
            'Null addresses object, api is not built properly')
        return res

    def _create_address(self, options):
        self._add_cleanup(self._delete_address, options['name'])
        cfg = self.cfg
        project_id = cfg.project_id
        region = cfg.region
        config = _prepare_address_create_parameters(**options)
        self.trace('Crete address with options {}'.format(config))
        request = self.addresses.insert(
            project=project_id,
            region=region,
            body=config)
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
        self._remove_cleanup(self._delete_address, name)
        self._execute_async_request(request, project_id, region=region)

    def _list_addresses(self):
        cfg = self.cfg
        project_id = cfg.project_id
        region = cfg.region
        self.trace('List addresses: project_id={} region={}'.
                   format(project_id, region))
        request = self.addresses.list(
            project=project_id,
            region=region)
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


class TestAddressesCRUD(TestAddressesBase):
    @property
    def addresses(self):
        res = self.api.compute.addresses()
        self.assertIsNotNone(
            res,
            'Null addresses object, api is not built properly')
        return res

    def setUp(self):
        super(TestAddressesCRUD, self).setUp()
        self._address_name = self._rand_name('testaddr')

    def _create(self):
        options = {
            'name': self._address_name
        }
        self._create_address(options)

    def _read(self):
        result = self._get_address(self._address_name)
        self.assertEqual(self._address_name, result['name'])
        result = self._list_addresses()
        self.assertFind(self._address_name, result)

    def _update(self):
        pass

    def _delete(self):
        self._delete_address(self._address_name)

    def test_crud(self):
        self._create()
        self._read()
        self._update()
        self._delete()
