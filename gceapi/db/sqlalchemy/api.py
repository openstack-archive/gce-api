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

"""Implementation of SQLAlchemy backend."""

import ast
import functools
import sys

from oslo_config import cfg
from oslo_db.sqlalchemy import session as db_session

import gceapi.context
from gceapi.db.sqlalchemy import models

CONF = cfg.CONF


_MASTER_FACADE = None


def _create_facade_lazily():
    global _MASTER_FACADE

    if _MASTER_FACADE is None:
        _MASTER_FACADE = db_session.EngineFacade.from_config(CONF)
    return _MASTER_FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def require_context(f):
    """Decorator to require *any* user or admin context.

    The first argument to the wrapped function must be the context.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        gceapi.context.require_context(args[0])
        return f(*args, **kwargs)
    return wrapper


def model_query(context, model, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param session: if present, the session to use
    """
    session = kwargs.get('session') or get_session()

    return session.query(model, *args).\
            filter_by(project_id=context.project_id)


@require_context
def add_item(context, kind, data):
    item_ref = models.Item()
    item_ref.update({
        "project_id": context.project_id,
        "kind": kind,
    })
    item_ref.update(_pack_item_data(data))
    item_ref.save()


@require_context
def delete_item(context, kind, item_id):
    model_query(context, models.Item).\
            filter_by(kind=kind,
                      id=item_id).\
            delete()


@require_context
def update_item(context, kind, item):
    item_ref = model_query(context, models.Item).\
            filter_by(kind=kind,
                      id=item["id"]).\
            one()
    item_ref.update(_pack_item_data(item))
    item_ref.save()


@require_context
def get_items(context, kind):
    return [_unpack_item_data(item)
            for item in model_query(context, models.Item).
                    filter_by(kind=kind).
                    all()]


@require_context
def get_item_by_id(context, kind, item_id):
    return _unpack_item_data(model_query(context, models.Item).
            filter_by(kind=kind,
                      id=item_id).
            first())


@require_context
def get_item_by_name(context, kind, name):
    return _unpack_item_data(model_query(context, models.Item).
            filter_by(kind=kind,
                      name=name).
            first())


def _pack_item_data(item_data):
    return {
        "id": item_data.pop("id"),
        "name": item_data.pop("name", None),
        "data": str(item_data),
    }


def _unpack_item_data(item_ref):
    if item_ref is None:
        return None
    data = ast.literal_eval(item_ref.data)
    data["id"] = item_ref.id
    if item_ref.name is not None:
        data["name"] = item_ref.name
    return data
