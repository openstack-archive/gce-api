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

import abc

from webob import exc

from gceapi.api import base_api
from gceapi.api import utils


class Scope(object):
    """Scope that contains resource.

    The following scopes exists: global, aggregated, zones, regions.
    """

    _type = None
    _collection = None
    _name = None

    @abc.abstractmethod
    def __init__(self, scope_name):
        self._name = scope_name

    def get_type(self):
        return self._type

    def get_name(self):
        return self._name

    def get_collection(self):
        return self._collection

    def get_path(self):
        if self._collection is not None and self._name is not None:
            return "/".join([self._collection, self._name])
        else:
            return self._type

    def get_scope_api(self):
        base_api.Singleton.get_instance(self.get_type())


class GlobalScope(Scope):

    _type = "global"

    def __init__(self):
        super(GlobalScope, self).__init__(None)


class AggregatedScope(Scope):

    _type = "aggregated"

    def __init__(self):
        super(AggregatedScope, self).__init__(None)


class ZoneScope(Scope):

    _type = "zone"
    _collection = utils.get_collection_name(_type)

    def __init__(self, scope_name):
        super(ZoneScope, self).__init__(scope_name)


class RegionScope(Scope):

    _type = "region"
    _collection = utils.get_collection_name(_type)

    def __init__(self, scope_name):
        super(RegionScope, self).__init__(scope_name)


def construct(scope_type, scope_id):
    if scope_type == "zone":
        return ZoneScope(scope_id)
    elif scope_type == "region":
        return RegionScope(scope_id)
    elif scope_type == "global":
        return GlobalScope()
    elif scope_type == "aggregated":
        return AggregatedScope()
    return None


def construct_from_path(path, scope_id):
    path_info = [item for item in path.split("/") if item]
    path_count = len(path_info)
    if path_count == 0:
        raise exc.HTTPBadRequest(comment="Bad path %s" % path)
    if path_count < 3:
        return None
    collection_or_type = path_info[1]
    if collection_or_type in ("zones", "regions") and scope_id is None:
        return None
    if collection_or_type == "zones":
        return ZoneScope(scope_id)
    elif collection_or_type == "regions":
        return RegionScope(scope_id)
    elif collection_or_type == "global":
        return GlobalScope()
    elif collection_or_type == "aggregated":
        return AggregatedScope()
    raise exc.HTTPBadRequest(comment="Bad path %s" % path)
