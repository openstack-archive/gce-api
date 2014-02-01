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

"""Defines interface for DB access.

Functions in this module are imported into the gceapi.db namespace. Call these
functions from gceapi.db namespace, not the gceapi.db.api namespace.

**Related Flags**

:dbackend:  string to lookup in the list of LazyPluggable backends.
            `sqlalchemy` is the only supported backend right now.

:connection:  string specifying the sqlalchemy connection to use, like:
              `sqlite:///var/lib/gceapi/gceapi.sqlite`.

"""

from gceapi.openstack.common.db import api as db_api


_BACKEND_MAPPING = {'sqlalchemy': 'gceapi.db.sqlalchemy.api'}
IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)


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
