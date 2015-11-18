# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import os
import threading
import webob

from oslo_config import cfg
from oslo_log import log as logging

from gceapi.api import clients
from gceapi import wsgi_ext as openstack_wsgi


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Controller(object):

    _lock = threading.RLock()
    _files = {}

    def discovery(self, req, version):
        """Returns appropriate json by its version."""

        key = version
        if key in self._files:
            return self._files[key]

        session = clients.admin_session()
        keystone = clients.keystone(None, session=session)
        if not keystone.has_service_catalog():
            keystone.authenticate(token=session.get_token())
        catalog = keystone.service_catalog.get_data()
        public_url = clients.get_url_from_catalog(catalog, "gceapi")
        if not public_url:
            public_url = req.host_url
        public_url = public_url.rstrip("/")

        self._lock.acquire()
        try:
            if key in self._files:
                return self._files[key]

            jfile = self._load_file(version)
            jfile = jfile.replace("{HOST_URL}", public_url)
            self._files[key] = jfile
            return jfile
        finally:
            self._lock.release()

    def _load_file(self, version):
        file = version + ".json"

        protocol_dir = CONF.get("protocol_dir")
        if protocol_dir:
            file_name = os.path.join(protocol_dir, file)
            try:
                f = open(file_name)
                result = f.read()
                f.close()
                return result
            except Exception as ex:
                pass

        # NOTE(apavlov): develop mode - try to find inside project
        # ../../etc/gceapi/protocols/
        current_file = os.path.abspath(inspect.getsourcefile(lambda _: None))
        current_dir = os.path.dirname(current_file)
        dir = os.path.join(current_dir, "../../etc/gceapi/protocols")
        file_name = os.path.join(dir, file)
        try:
            f = open(file_name)
        except Exception as ex:
            raise webob.exc.HTTPNotFound(ex)
        result = f.read()
        f.close()
        return result


def create_resource():
    return openstack_wsgi.Resource(Controller())
