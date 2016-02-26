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
import os
import re
import string
import time
import traceback
import urlparse

from googleapiclient import discovery
from googleapiclient import schema
import jsonschema
from oslo_log import log as logging
from tempest.lib import base
from tempest.lib.common.utils import data_utils

from gceapi.tests.functional import config
from gceapi.tests.functional import credentials


CONF = config.CONF
LOG = logging.getLogger("gceapi")
API_NAME = 'compute'
API_VER = 'v1'


def trace(msg):
    LOG.debug(msg)


def safe_call(method):
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as err:
            trace('Exception {}'.format(err))
            bt = traceback.format_exc()
            trace('Exception  back trace {}'.format(bt))
        return None
    return wrapper


def string_to_re_pattern(s):
    _SYMBOLS = '.+'
    res = s
    for i in _SYMBOLS:
        res = res.replace(i, '\{}'.format(i))
    return res


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


class SchemaHolder(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SchemaHolder, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    _schema = None

    def get_schema(self, schema_file):
        if self._schema:
            return self._schema

        schema_path = os.path.join(config.get_base_dir(), schema_file)
        # Load API scheme for API calls validation
        with open(schema_path, 'r') as f:
            self._schema = json.load(f)

        return self._schema


class GCEApi(object):
    def __init__(self, cred_provider):
        self._compute = None
        self._cred_provider = cred_provider
        self._schema = None
        self._scheme_ref_resolver = 0

    def init(self):
        _schema = SchemaHolder().get_schema(CONF.gce.schema)
        self._schema = schema.Schemas(_schema)
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
    def compute(self):
        assert(self._compute is not None)
        return self._compute

    def validate_schema(self, value, schema_name):
        schema = self._schema.get(schema_name)
        jsonschema.validate(value, schema, resolver=self._scheme_ref_resolver)

    @staticmethod
    def _is_absolute_url(url):
        return bool(urlparse.urlparse(url).netloc)

    @staticmethod
    def _is_standard_port(protocol, port):
        _map = {'http': 80, 'https': 443}
        return _map[protocol] == port

    @property
    def _host_url(self):
        cfg = CONF.gce
        if not cfg.port or self._is_standard_port(cfg.protocol, cfg.port):
            return '{}://{}'.format(cfg.protocol, cfg.host)
        return '{}://{}:{}'.format(cfg.protocol, cfg.host, cfg.port)

    @property
    def _discovery_url(self):
        t = '{}{}' if CONF.gce.discovery_url.startswith('/') else '{}/{}'
        return t.format(self._host_url, CONF.gce.discovery_url)

    @property
    def _api_url(self):
        return '{}/{}/{}'.format(self._host_url, API_NAME, API_VER)

    @property
    def project_url(self):
        return '{}/projects/{}'.format(self._api_url, CONF.gce.project_id)

    def get_zone_url(self, resource=None, zone=None):
        if resource and self._is_absolute_url(resource):
            return resource
        z = zone
        if z is None:
            z = CONF.gce.zone
        if not self._is_absolute_url(z):
            t = '{}/{}' if z.startswith('zones/') else '{}/zones/{}'
            z = t.format(self.project_url, z)
        if not resource:
            return z
        return '{}/{}'.format(z, resource)

    def get_region_url(self, resource=None, region=None):
        if resource and self._is_absolute_url(resource):
            return resource
        r = region
        if r is None:
            r = CONF.gce.region
        if not self._is_absolute_url(r):
            t = '{}/{}' if r.startswith('regions/') else '{}/regions/{}'
            r = t.format(self.project_url, r)
        if not resource:
            return r
        return '{}/{}'.format(r, resource)

    def get_global_url(self, resource):
        if self._is_absolute_url(resource):
            return resource
        t = '{}/{}' if resource.startswith('projects/') else '{}/projects/{}'
        return t.format(self._api_url, resource)

    def get_project_url(self, resource):
        if self._is_absolute_url(resource):
            return resource
        t = '{}/{}'
        return t.format(self.project_url, resource)


class GCETestCase(base.BaseTestCase):
    @property
    def api(self):
        if self._api is None:
            self.fail('Api object is None - test is not initialized properly')
        return self._api

    @property
    def cfg(self):
        return CONF.gce

    @staticmethod
    def trace(msg):
        trace(msg)

    @staticmethod
    def trace_request(request):
        trace('Request: {}'.format(request.to_json()))

    @classmethod
    def setUpClass(cls):
        cls._credentials_provider = credentials.CredentialsProvider(CONF.gce)
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

    def assertNotFind(self, item, items_list, key='items'):
        found = None
        items = []
        if key in items_list:
            items = items_list[key]
            for i in items:
                if i['name'] == item:
                    found = i
                    break

        if found:
            msg = 'There is item {} that should not be in the list {}'
            self.fail(msg.format(item, items))

    def _match_values(self, key, expected, actual):
        missing = []
        mismatched = []
        if isinstance(expected, dict) and isinstance(actual, dict):
            missing, mismatched = self._match_objects(expected,
                                                      actual,
                                                      root_key=key)
        elif isinstance(expected, list) and isinstance(actual, list):
            expected.sort()
            actual.sort()
            if len(expected) > len(actual):
                _missing = [str(i) for i in expected[len(actual):]]
                msg = 'key={}: subitems: {}'.format(key, ', '.join(_missing))
                missing.append(msg)
            for e, a in zip(expected, actual):
                _missing, _mismatched = self._match_values(key, e, a)
                missing.extend(_missing)
                mismatched.extend(_mismatched)
        elif isinstance(expected, (str, unicode, buffer)):
            if not re.compile(expected).match(str(actual)):
                msg = 'key={}: actual={}: expected_regexp={}'
                mismatched.append(msg.format(key, actual, expected))
        elif type(expected) == type(actual):
            if expected != actual:
                msg = 'key={}: actual={}: expected={}'
                mismatched.append(msg.format(key, actual, expected))
        else:
            msg = 'key={}: mismatched object types: actual={}: expected={}'
            mismatched.append(msg.format(key, type(actual), type(expected)))
        return missing, mismatched

    def _match_objects(self, expected, actual, root_key=None):
        missing = []
        mismatched = []
        for key, value in expected.items():
            if key not in actual:
                missing.append(key)
            else:
                _key = '{}/{}'.format(root_key, key) if root_key else key
                _missing, _mismatched = self._match_values(_key,
                                                           value, actual[key])
                missing.extend(_missing)
                mismatched.extend(_mismatched)
        return missing, mismatched

    def assertObject(self, expected, actual):
        self.trace('Validate object: \n\texpected: {}\n\tactual: {}'.
                   format(expected, actual))
        missing, mismatched = self._match_objects(expected, actual)
        err = ''
        if missing:
            err = 'Missing: {}'.format(', '.join(m for m in missing))
        if mismatched:
            if err:
                err += '; '
            err += 'Mismatched values: {}'.format(', '.join(mismatched))
        if err:
            self.fail(err)

    @property
    def full_compatibility(self):
        return self._credentials_provider.is_google_auth

    @property
    def is_nova_network(self):
        return self.cfg.networking == 'nova-network'

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
        if v in self._cleanups:
            self._cleanups.remove(v)

    def _execute_async_request(self, request, project, zone=None, region=None):
        self.trace_request(request)
        operation = request.execute()
        name = operation['name']
        self.trace('Waiting for operation {} to finish...'.format(name))
        begin = time.time()
        timeout = self.cfg.build_timeout
        interval = self.cfg.build_interval
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
            time.sleep(interval)
        self.fail('Request {} failed with timeout {},'
                  ' latest operation status {}'.format(name, timeout, result))


def insert_json_parameters(obj, **kwargs):
    s = json.dumps(obj)
    t = string.Template(s)
    s = t.substitute(**kwargs)
    return json.loads(s)
