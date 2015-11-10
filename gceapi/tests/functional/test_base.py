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

import json
import string
import time
import traceback
import urlparse

from googleapiclient import discovery
from googleapiclient import schema
import jsonschema
from oslo_log import log as logging
from tempest_lib import base
from tempest_lib.common.utils import data_utils

from gceapi.tests.functional import config
from gceapi.tests.functional import credentials


CONF = config.CONF.gce
LOG = logging.getLogger("gceapi")
API_NAME = 'compute'
API_VER = 'v1'


def trace(msg):
    LOG.debug(msg)


def safe_call(method):
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as err:
            trace('Exception {}'.format(err))
            bt = traceback.format_exc()
            trace('Exception  back trace {}'.format(bt))
        return None
    return wrapper


class LocalRefResolver(jsonschema.RefResolver):
    def __init__(
            self,
            base_uri,
            referrer,
            store=(),
            cache_remote=True,
            handlers=(),
            urljoin_cache=None,
            remote_cache=None):
        super(LocalRefResolver, self).__init__(base_uri,
                                               referrer,
                                               store,
                                               cache_remote,
                                               handlers,
                                               urljoin_cache,
                                               remote_cache)
        self._local_schema = referrer

    def resolve_from_url(self, url):
        if url in self._local_schema:
            return self._local_schema[url]
        return super(LocalRefResolver, self).resolve_from_url(url)


class GCEApi(object):
    def __init__(self, cred_provider):
        self._compute = None
        self._cred_provider = cred_provider
        self._schema = None
        self._scheme_ref_resolver = 0

    def init(self):
        self._schema = schema.Schemas(CONF.schema)
        self._scheme_ref_resolver = LocalRefResolver.from_schema(
            self._schema.schemas)
        self._build_api()

    def _build_api(self):
        credentials = self._cred_provider.credentials
        url = self._discovery_url
        trace('Build Google compute api with discovery url {}'.format(url))
        self._compute = discovery.build(
            API_NAME,
            API_VER,
            credentials=credentials,
            discoveryServiceUrl=url
        )

    @property
    def _discovery_url(self):
        cfg = CONF
        return '{}://{}:{}{}'.format(
            cfg.protocol,
            cfg.host,
            cfg.port,
            cfg.discovery_url
        )

    @property
    def compute(self):
        assert(self._compute is not None)
        return self._compute

    @property
    def api_url(self):
        cfg = CONF
        return '{}://{}/{}/{}'.format(
            cfg.protocol,
            cfg.host,
            API_NAME,
            API_VER)

    def validate_schema(self, value, schema_name):
        schema = self._schema.get(schema_name)
        jsonschema.validate(value, schema, resolver=self._scheme_ref_resolver)

    @property
    def project_url(self):
        return '{}/projects/{}'.format(self.api_url, CONF.project_id)

    def get_zone_url(self, zone=None):
        z = zone
        if z is None:
            z = CONF.zone
        if self.is_absolute(z):
            return z
        t = '{}/{}' if z.startswith('zones/') else '{}/zones/{}'
        return t.format(self.project_url, z)

    def get_resource_url(self, resource, zone=None):
        if self.is_absolute(resource):
            return resource
        return '{}/{}'.format(self.get_zone_url(zone=zone), resource)

    def get_global_url(self, resource):
        if self.is_absolute(resource):
            return resource
        t = '{}/{}' if resource.startswith('projects/') else '{}/projects/{}'
        return t.format(self.api_url, resource)

    def get_project_url(self, resource):
        if self.is_absolute(resource):
            return resource
        t = '{}/{}'
        return t.format(self.project_url, resource)

    @staticmethod
    def is_absolute(url):
        return bool(urlparse.urlparse(url).netloc)


class GCETestCase(base.BaseTestCase):
    @property
    def api(self):
        if self._api is None:
            self.fail('Api object is None - test is not initialized properly')
        return self._api

    @property
    def cfg(self):
        return CONF

    @staticmethod
    def trace(msg):
        trace(msg)

    @staticmethod
    def trace_request(request):
        trace('Request: {}'.format(request.to_json()))

    @classmethod
    def setUpClass(cls):
        cls._credentials_provider = credentials.CredentialsProvider(CONF)
        cls._api = GCEApi(cls._credentials_provider)
        cls._api.init()
        super(GCETestCase, cls).setUpClass()

    def assertFind(self, item, items_list, key='items'):
        items = []
        if key in items_list:
            items = items_list[key]
            for i in items:
                if i['name'] == item:
                    return i
        self.fail(
            'There is no required item {} in the list {}'.format(item, items))

    def assertObject(self, expected, observed):
        self.trace('Validate object: \n\texpected: {}\n\tobserved: {}'.
                   format(expected, observed))
        observed_keys = observed.keys()
        for item in expected.items():
            key = item[0]
            value = item[1]
            if value is None:
                self.assertNotIn(key, observed_keys)
            else:
                self.assertIn(key, observed_keys)
                self.assertEqual(value, observed[key])

    @property
    def is_real_gce(self):
        return self._credentials_provider.is_google_auth

    def _get_operations_request(self, name, project, zone, region):
        if zone is not None:
            return self.api.compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=name)
        if region is not None:
            return self.api.compute.regionOperations().get(
                project=project,
                region=region,
                operation=name)
        return self.api.compute.globalOperations().get(
                project=project,
                operation=name)

    @staticmethod
    def _rand_name(prefix='n-'):
        return data_utils.rand_name(prefix)

    def _add_cleanup(self, method, *args, **kwargs):
        self.addCleanup(method, *args, **kwargs)

    @safe_call
    def _remove_cleanup(self, method, *args, **kwargs):
        v = (method, args, kwargs)
        self._cleanups.remove(v)

    def _execute_async_request(self, request, project, zone=None, region=None):
        self.trace_request(request)
        operation = request.execute()
        name = operation['name']
        self.trace('Waiting for operation {} to finish...'.format(name))
        begin = time.time()
        timeout = self.cfg.build_timeout
        result = None
        while time.time() - begin < timeout:
            result = self._get_operations_request(
                name, project, zone, region).execute()
            self.api.validate_schema(value=result, schema_name='Operation')
            if result['status'] == 'DONE':
                if 'error' in result:
                    self.fail('Request {} failed with error {}'. format(
                        name, result['error']))
                else:
                    self.trace("Request {} done successfully".format(name))
                return
            time.sleep(1)

        self.fail('Request {} failed with timeout {},'
                  ' latest operation status {}'.format(name, timeout, result))


def insert_json_parameters(obj, **kwargs):
    s = json.dumps(obj)
    t = string.Template(s)
    s = t.substitute(**kwargs)
    return json.loads(s)
