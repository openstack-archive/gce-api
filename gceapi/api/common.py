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

"""Base GCE API controller"""

import os.path
import re
from webob import exc

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import timeutils

from gceapi.api import clients
from gceapi.api import operation_api
from gceapi.api import operation_util
from gceapi.api import scopes
from gceapi.api import utils
from gceapi import exception
from gceapi.i18n import _

LOG = logging.getLogger(__name__)
FLAGS = cfg.CONF


class Controller(object):
    """Base controller

    Implements base CRUD methods.
    Individual GCE controllers should inherit this and:
    - implement format_item() method,
    - override _get_type() method,
    - add necessary specific request handlers,
    - use _api to hold instance of related GCE API (see base_api.py).
    """

    _api = None

    # Initialization
    def __init__(self, api):
        """Base initialization.

        Inherited classes should init _api and call super().
        """

        self._api = api
        self._type_name = self._api._get_type()
        self._collection_name = utils.get_collection_name(self._type_name)
        self._type_kind = utils.get_type_kind(self._type_name)
        self._list_kind = utils.get_list_kind(self._type_name)
        self._aggregated_kind = utils.get_aggregated_kind(self._type_name)
        self._operation_api = operation_api.API()

    def process_result(self, request, action, action_result):
        context = self._get_context(request)
        operation = operation_util.save_operation(context, action_result)
        if operation is not None:
            scope = self._operation_api.get_scopes(context, operation)[0]
            action_result = self._format_operation(request, operation, scope)

        if isinstance(action_result, Exception):
            return self._format_error(action_result)
        if action_result is None:
            return None, 204
        return self._format_output(request, action, action_result), 200

    # Base methods, should be overriden

    def format_item(self, request, image, scope):
        """Main item resource conversion routine

        Overriden in inherited classes should implement conversion of
        OpenStack resource into GCE resource.
        """

        raise exc.HTTPNotImplemented

    # Actions
    def index(self, req, scope_id=None):
        """GCE list requests, global or with zone/region specified."""

        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)

        items = self._api.get_items(context, scope)
        items = [{
            "scope": scope,
            "item": self.format_item(req, i, scope)
        } for i in items]
        items = self._filter_items(req, items)
        items, next_page_token = self._page_items(req, items)
        items = [i["item"] for i in items]

        return self._format_list(req, items, next_page_token, scope)

    def show(self, req, id=None, scope_id=None):
        """GCE get requests, global or zone/region specified."""

        context = self._get_context(req)
        scope = self._get_scope(req, scope_id)
        try:
            item = self._api.get_item(context, id, scope)
            return self.format_item(req, item, scope)
        except (exception.NotFound, KeyError, IndexError) as ex:
            LOG.exception(ex)
            msg = _("Resource '%s' could not be found") % id
            raise exc.HTTPNotFound(explanation=msg)

    def aggregated_list(self, req):
        """GCE aggregated list requests for all zones/regions."""

        context = self._get_context(req)
        items = list()
        for item in self._api.get_items(context, None):
            for scope in self._api.get_scopes(context, item):
                items.append({
                    "scope": scope,
                    "item": self.format_item(req, item, scope)
                })
        items = self._filter_items(req, items)
        items, next_page_token = self._page_items(req, items)

        items_by_scopes = {}
        for item in items:
            scope_path = item["scope"].get_path()
            items_by_scope = items_by_scopes.setdefault(scope_path,
                {self._collection_name: []})[self._collection_name]
            items_by_scope.append(item["item"])

        return self._format_list(req, items_by_scopes, next_page_token,
            scopes.AggregatedScope())

    def delete(self, req, id, scope_id=None):
        """GCE delete requests."""

        scope = self._get_scope(req, scope_id)
        context = self._get_context(req)
        operation_util.init_operation(context, "delete",
                                      self._type_name, id, scope)
        try:
            self._api.delete_item(context, id, scope)
        except (exception.NotFound, KeyError, IndexError) as ex:
            LOG.exception(ex)
            msg = _("Resource '%s' could not be found") % id
            raise exc.HTTPNotFound(explanation=msg)

    def create(self, req, body, scope_id=None):
        """GCE add requests."""

        scope = self._get_scope(req, scope_id)
        context = self._get_context(req)
        operation_util.init_operation(context, "insert",
                                      self._type_name, body["name"], scope)
        self._api.add_item(context, body['name'], body, scope)

    # Filtering
    def _filter_items(self, req, items):
        """Filtering result list

        Only one filter is supported(eg. by one field)
        Only two comparison strings are supported: 'eq' and 'ne'
        There are no logical expressions with fields
        """
        if not items:
            return items
        if "filter" not in req.params:
            return items

        filter_def = req.params["filter"].split()
        if len(filter_def) != 3:
            # TODO(apavlov): raise exception
            return items
        if filter_def[1] != "eq" and filter_def[1] != "ne":
            # TODO(apavlov): raise exception
            return items
        if filter_def[0] not in items[0]["item"]:
            # TODO(apavlov): raise exception
            return items

        filter_field = filter_def[0]
        filter_cmp = filter_def[1] == "eq"
        filter_pattern = filter_def[2]
        if filter_pattern[0] == "'" and filter_pattern[-1] == "'":
            filter_pattern = filter_pattern[1:-1]

        result_list = list()
        for item in items:
            field = item["item"][filter_field]
            result = re.match(filter_pattern, field)
            if filter_cmp != (result is None):
                result_list.append(item)

        return result_list

    # Paging
    def _page_items(self, req, items):
        if not items:
            return items, None
        if "maxResults" not in req.params:
            return items, None

        limit = int(req.params["maxResults"])
        if limit >= len(items):
            return items, None

        page_index = int(req.params.get("pageToken", 0))
        if page_index < 0 or page_index * limit > len(items):
            # TODO(apavlov): raise exception
            return [], None

        items.sort(None, lambda x: x["item"].get("name"))
        start = limit * page_index
        if start + limit >= len(items):
            return items[start:], None

        return items[start:start + limit], str(page_index + 1)

    # Utility
    def _get_context(self, req):
        return req.environ['gceapi.context']

    def _get_scope(self, req, scope_id):
        scope = scopes.construct_from_path(req.path_info, scope_id)
        if scope is None:
            return None
        scope_api = scope.get_scope_api()
        if scope_api is not None:
            try:
                context = self._get_context(req)
                scope_api.get_item(context, scope.get_name(), None)
            except ValueError as ex:
                raise exc.HTTPNotFound(detail=ex)

        return scope

    # Result formatting
    def _format_date(self, date_string):
        """Returns standard format for given date."""
        if date_string is None:
            return None
        if isinstance(date_string, basestring):
            date_string = timeutils.parse_isotime(date_string)
        return date_string.strftime('%Y-%m-%dT%H:%M:%SZ')

    def _get_id(self, link):
        hashed_link = hash(link)
        if hashed_link < 0:
            hashed_link = -hashed_link
        return str(hashed_link)

    def _qualify(self, request, controller, identifier, scope):
        """Creates fully qualified selfLink for an item or collection

        Specific formatting for projects and zones/regions,
        'global' prefix For global resources,
        'zones/zone_id' prefix for zone(similar for regions) resources.
        """

        context = self._get_context(request)
        public_url = clients.url_for(context, "gceapi")
        if public_url:
            public_url = public_url.rstrip("/") + "/"\
                + request.script_name.lstrip("/")
        else:
            public_url = request.application_url

        result = os.path.join(
            public_url, context.project_name)
        if controller:
            if scope:
                result = os.path.join(result, scope.get_path())
            result = os.path.join(result, controller)
            if identifier:
                result = os.path.join(result, identifier)
        return result

    def _format_item(self, request, result_dict, scope):
        return self._add_item_header(request, result_dict, scope,
                                     self._type_kind, self._collection_name)

    def _format_operation(self, request, operation, scope):
        result_dict = {
            "name": operation["name"],
            "operationType": operation["type"],
            "insertTime": operation["insert_time"],
            "startTime": operation["start_time"],
            "status": operation["status"],
            "progress": operation["progress"],
            "user": operation["user"],
        }
        result_dict["targetLink"] = self._qualify(
                request, utils.get_collection_name(operation["target_type"]),
                operation["target_name"], scope)
        result_dict["targetId"] = self._get_id(result_dict["targetLink"])
        if "end_time" in operation:
            result_dict["endTime"] = operation["end_time"]
        if "error_code" in operation:
            result_dict.update({
                "httpErrorStatusCode": operation["error_code"],
                "httpErrorMessage": operation["error_message"],
                "error": {"errors": operation["errors"]},
            })
        type_name = self._operation_api._get_type()
        return self._add_item_header(request, result_dict, scope,
                                     utils.get_type_kind(type_name),
                                     utils.get_collection_name(type_name))

    def _add_item_header(self, request, result_dict, scope,
                         _type_kind, _collection_name):
        if scope is not None and scope.get_name() is not None:
            result_dict[scope.get_type()] = self._qualify(
                    request, scope.get_collection(), scope.get_name(), None)
        result_dict["kind"] = _type_kind
        result_dict["selfLink"] = self._qualify(
                request, _collection_name, result_dict.get("name"), scope)
        result_dict["id"] = self._get_id(result_dict["selfLink"])
        return result_dict

    def _format_list(self, request, result_list, next_page_token, scope):
        result_dict = {}
        result_dict["items"] = result_list
        if next_page_token:
            result_dict["nextPageToken"] = next_page_token
        result_dict["kind"] = (self._aggregated_kind
            if scope and isinstance(scope, scopes.AggregatedScope)
            else self._list_kind)

        context = self._get_context(request)
        list_id = os.path.join("projects", context.project_name)
        if scope:
            list_id = os.path.join(list_id, scope.get_path())
        list_id = os.path.join(list_id, self._collection_name)
        result_dict["id"] = list_id

        result_dict["selfLink"] = self._qualify(
                request, self._collection_name, None, scope)
        return result_dict

    def _format_error(self, ex_value):
        if isinstance(ex_value, exception.NotAuthorized):
            msg = _('Unauthorized')
            code = 401
        elif isinstance(ex_value, exc.HTTPException):
            msg = ex_value.explanation
            code = ex_value.code
        elif isinstance(ex_value, exception.GceapiException):
            msg = ex_value.args[0]
            code = ex_value.code
        else:
            msg = _('Internal server error')
            code = 500

        return {
            'error': {'errors': [{'message': msg}]},
            'code': code,
            'message': msg
            }, code

    def _format_output(self, request, action, action_result):
        # TODO(ft): this metod must be safe and ignore unknown fields
        fields = request.params.get('fields', None)
        # TODO(ft): GCE can also format results of other action
        if action not in ('index', 'show') or fields is None:
            return action_result

        if action == 'show':
            action_result = utils.apply_template(fields, action_result)
            return action_result
        sp = utils.split_by_comma(fields)
        top_level = []
        items = []
        for string in sp:
            if 'items' in string:
                items.append(string)
            else:
                top_level.append(string)
        res = {}
        if len(items) > 0:
            res['items'] = []
        for string in top_level:
            dct = utils.apply_template(string, action_result)
            for key, val in dct.items():
                res[key] = val
        for string in items:
            if '(' in string:
                dct = utils.apply_template(string, action_result)
                for key, val in dct.items():
                    res[key] = val
            elif string.startswith('items/'):
                string = string[len('items/'):]
                for element in action_result['items']:
                    dct = utils.apply_template(string, element)
                    res['items'].append(dct)

        return res
