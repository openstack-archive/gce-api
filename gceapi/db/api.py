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

"""Defines interface for DB access.

Functions in this module are imported into the gceapi.db namespace. Call these
functions from gceapi.db namespace, not the gceapi.db.api namespace.

**Related Flags**

:dbackend:  string to lookup in the list of LazyPluggable backends.
            `sqlalchemy` is the only supported backend right now.

:connection:  string specifying the sqlalchemy connection to use, like:
              `sqlite:///var/lib/gceapi/gceapi.sqlite`.

"""

from eventlet import tpool
from oslo_config import cfg
from oslo_db import api as db_api
from oslo_log import log as logging


tpool_opts = [
    cfg.BoolOpt('use_tpool',
                default=False,
                deprecated_name='dbapi_use_tpool',
                deprecated_group='DEFAULT',
                help='Enable the experimental use of thread pooling for '
                     'all DB API calls'),
]

CONF = cfg.CONF
CONF.register_opts(tpool_opts, 'database')

_BACKEND_MAPPING = {'sqlalchemy': 'gceapi.db.sqlalchemy.api'}


class GCEDBAPI(object):
    """gce's DB API wrapper class.

    This wraps the oslo DB API with an option to be able to use eventlet's
    thread pooling. Since the CONF variable may not be loaded at the time
    this class is instantiated, we must look at it on the first DB API call.
    """

    def __init__(self):
        self.__db_api = None

    @property
    def _db_api(self):
        if not self.__db_api:
            gce_db_api = db_api.DBAPI(CONF.database.backend,
                                      backend_mapping=_BACKEND_MAPPING)
            if CONF.database.use_tpool:
                self.__db_api = tpool.Proxy(gce_db_api)
            else:
                self.__db_api = gce_db_api
        return self.__db_api

    def __getattr__(self, key):
        return getattr(self._db_api, key)


IMPL = GCEDBAPI()

LOG = logging.getLogger(__name__)


def add_item(context, kind, data):
    IMPL.add_item(context, kind, data)


def delete_item(context, kind, item_id):
    IMPL.delete_item(context, kind, item_id)


def update_item(context, kind, item):
    IMPL.update_item(context, kind, item)


def get_items(context, kind):
    return IMPL.get_items(context, kind)


def get_item_by_id(context, kind, item_id):
    return IMPL.get_item_by_id(context, kind, item_id)


def get_item_by_name(context, kind, name):
    return IMPL.get_item_by_name(context, kind, name)
