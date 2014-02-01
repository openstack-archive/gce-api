#    Copyright 2013 Cloudscaling Group, Inc
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

import inspect
import os
import threading
import webob

from gceapi import wsgi_ext as openstack_wsgi
from gceapi.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class Controller(object):

    _lock = threading.RLock()
    _files = {}

    def discovery(self, req, version):
        """Returns appropriate json by its version"""

        if version in self._files:
            return self._files[version]

        self._lock.acquire()
        try:
            if version in self._files:
                return self._files[version]

            jfile = self._load_file(version)
            jfile = jfile.replace("{HOST_URL}", req.host_url)
            self._files[version] = jfile
            return jfile
        finally:
            self._lock.release()

    def _load_file(self, version):
        current_file = os.path.abspath(inspect.getsourcefile(lambda _: None))
        current_dir = os.path.dirname(current_file)
        file_name = os.path.join(current_dir, "compute", version + ".json")
        try:
            f = open(file_name)
        except Exception as ex:
            raise webob.exc.HTTPNotFound(ex)
        result = f.read()
        f.close()
        return result


def create_resource():
    return openstack_wsgi.Resource(Controller())
