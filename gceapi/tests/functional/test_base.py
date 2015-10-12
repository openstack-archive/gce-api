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
from tempest_lib import base


class TestSupp(object):
    def __init__(self, *args, **kwargs):
        self._cfg = config.CONF.gce
        from oslo_log import log as logging
        self._log = logging.getLogger(self._cfg.logger_name)

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
        self._auth()
        self._build_api()

    def _auth(self):
        from oauth2client.client import GoogleCredentials
        self.supp.trace('Create GoogleCredentials from default app file')
        self.credentials = GoogleCredentials.get_application_default()

    def _build_api(self):
        from googleapiclient.discovery import build
        self.supp.trace('Build Google compute api')
        self._compute = build('compute', 'v1', credentials=self.credentials)

    @property
    def compute(self):
        assert(self._compute is not None)
        return self._compute

    @property
    def supp(self):
        assert(self._supp is not None)
        return self._supp


class GCETestCase(base.BaseTestCase):
    def __init__(self, *args, **kwargs):
        self._supp = TestSupp()
        self._api = GCEApi(self._supp)
        super(GCETestCase, self).__init__(*args, **kwargs)

    @property
    def cfg(self):
        return self._supp.cfg

    @property
    def api(self):
        assert(self._api is not None)
        return self._api

    def trace(self, *args, **kwargs):
        self._supp.trace(*args, **kwargs)

    def setUp(self):
        self.api.init()
        super(GCETestCase, self).setUp()
