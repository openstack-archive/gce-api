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


from googleapiclient.discovery import build
from googleapiclient.schema import Schemas
from jsonschema import RefResolver
from jsonschema import validate
from tempest_lib import base

from gceapi.tests.functional import config
from gceapi.tests.functional.credentials import CredentialsProvider


class TestSupp(object):
    def __init__(self, *args, **kwargs):
        self._cfg = config.CONF.gce
        from oslo_log import log as logging
        self._log = logging.getLogger("gceapi")

    @property
    def cfg(self):
        return self._cfg

    def trace(self, *args, **kwargs):
        print(args, kwargs)
        self._log.trace(*args, **kwargs)


class LocalRefResolver(RefResolver):
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
    def __init__(self, supp, cred_provider):
        self._compute = None
        self._cred_provider = cred_provider
        self._schema = None
        self._scheme_ref_resolver = 0
        self._supp = supp

    def init(self):
        self._schema = Schemas(self._supp.cfg.schema)
        self._scheme_ref_resolver = LocalRefResolver.from_schema(
            self._schema.schemas)
        self._build_api()

    def _build_api(self):
        credentials = self._cred_provider.credentials
        url = self._discovery_url
        self._trace(
            'Build Google compute api with discovery url {}'.format(url))
        self._compute = build(
            'compute', 'v1',
            credentials=credentials,
            discoveryServiceUrl=url
        )

    @property
    def _discovery_url(self):
        cfg = self._supp.cfg
        return '{}://{}:{}{}'.format(
            cfg.protocol,
            cfg.host,
            cfg.port,
            cfg.discovery_url
        )

    def _trace(self, msg):
        self._supp.trace(msg)

    @property
    def compute(self):
        assert(self._compute is not None)
        return self._compute

    def validate_schema(self, value, schema_name):
        schema = self._schema.get(schema_name)
        validate(value, schema, resolver=self._scheme_ref_resolver)


class GCETestCase(base.BaseTestCase):
    @property
    def cfg(self):
        assert(self._supp.cfg is not None)
        return self._supp.cfg

    @property
    def api(self):
        assert(self._api is not None)
        return self._api

    def trace(self, *args, **kwargs):
        self._supp.trace(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls._supp = TestSupp()
        cls._api = GCEApi(cls._supp, CredentialsProvider(cls._supp))
        cls._api.init()
        super(GCETestCase, cls).setUpClass()

    def assertFind(self, item, items_list):
        found = False
        items = items_list['items']
        for i in items:
            if i['name'] == item:
                found = True
                break

        self.assertIs(
            True,
            found,
            'There is no required item {} in the list {}'.format(item, items))
