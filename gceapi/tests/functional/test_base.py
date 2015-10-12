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


from gceapi.tests.functional import config
from googleapiclient.discovery import build
from googleapiclient.schema import Schemas
from jsonschema import validate
from oauth2client.client import GoogleCredentials
from tempest_lib import base


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


class GCEApi(object):
    def __init__(self, supp):
        self._supp = supp
        self._schema = None
        self._compute = None

    def init(self):
        self._schema = Schemas(self._supp.cfg.schema)
        self._auth()
        self._build_api()

    def _auth(self):
        self._trace('Create GoogleCredentials from default app file')
        self.credentials = GoogleCredentials.get_application_default()

    def _build_api(self):
        url = self._get_discovery_url()
        self._trace(
            'Build Google compute api with discovery url {}'.format(url))
        self._compute = build(
            'compute', 'v1',
            credentials=self.credentials,
            discoveryServiceUrl=url
        )

    def _get_discovery_url(self):
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
        validate(value, self._schema[schema_name])


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
        cls._api = GCEApi(cls._supp)
        cls._api.init()
        super(GCETestCase, cls).setUpClass()
