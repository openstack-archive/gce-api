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
            'compute', 'v1',
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
    def base_url(self):
        cfg = CONF
        return '{}://{}:{}'.format(
            cfg.protocol,
            cfg.host,
            cfg.port
        )

    def validate_schema(self, value, schema_name):
        schema = self._schema.get(schema_name)
        jsonschema.validate(value, schema, resolver=self._scheme_ref_resolver)


class GCETestCase(base.BaseTestCase):
    @property
    def api(self):
        assert(self._api is not None)
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
        cp = credentials.CredentialsProvider(CONF)
        cls._api = GCEApi(cp)
        cls._api.init()
        super(GCETestCase, cls).setUpClass()

    def assertFind(self, item, items_list):
        key = 'items'
        items = []
        if key in items_list:
            items = items_list[key]
            for i in items:
                if i['name'] == item:
                    return
        self.fail(
            'There is no required item {} in the list {}'.format(item, items))

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
