# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gceapi.auth
import gceapi.context
import gceapi.db.api
import gceapi.exception
import gceapi.paths
import gceapi.service
import gceapi.wsgi
import itertools


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(
             gceapi.auth.auth_opts,
             gceapi.context.gce_opts,
             gceapi.db.api.tpool_opts,
             gceapi.exception.exc_log_opts,
             gceapi.paths.path_opts,
             gceapi.service.service_opts,
             gceapi.wsgi.wsgi_opts,
         )),
    ]
