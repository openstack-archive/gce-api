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

import uuid

from oslo_utils import timeutils

from gceapi.api import base_api
from gceapi.api import scopes
from gceapi import exception
from gceapi.i18n import _


class API(base_api.API):
    """GCE operation API."""

    KIND = "operation"
    PERSISTENT_ATTRIBUTES = ["id", "insert_time", "start_time", "end_time",
                             "name", "type", "user", "status", "progress",
                             "scope_type", "scope_name",
                             "target_type", "target_name",
                             "method_key", "item_id",
                             "error_code", "error_message", "errors"]

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)
        method = base_api.API._get_complex_operation_progress
        self._method_keys = {method: "complex_operation"}
        self._get_progress_methods = {"complex_operation": method}

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def register_get_progress_method(self, method_key, method):
        if method_key in self._get_progress_methods:
            raise exception.Invalid()
        # TODO(ft): check 'method' formal arguments
        self._method_keys[method] = method_key
        self._get_progress_methods[method_key] = method

    def get_scopes(self, context, item):
        return [scopes.construct(item["scope_type"], item["scope_name"])]

    def get_item(self, context, name, scope=None):
        operation = self._get_db_item_by_name(context, name)
        if (operation is None or
                operation["scope_type"] != scope.get_type() or
                operation["scope_name"] != scope.get_name()):
            raise exception.NotFound
        operation = self._update_operation_progress(context, operation)
        return operation

    def get_items(self, context, scope=None):
        operations = self._get_db_items(context)
        if scope is not None:
            operations = [operation for operation in operations
                          if (operation["scope_type"] == scope.get_type() and
                              operation["scope_name"] == scope.get_name())]
        for operation in operations:
            operation = self._update_operation_progress(context, operation)
        return operations

    def delete_item(self, context, name, scope=None):
        # NOTE(ft): Google deletes operation with no check it's scope
        item = self._get_db_item_by_name(context, name)
        if item is None:
            raise exception.NotFound
        self._delete_db_item(context, item)

    # TODO(apavlov): rework updating end_time field
    # now it updates only by user request that may occurs
    # after a long period of time
    def _update_operation_progress(self, context, operation):
        if operation["status"] == "DONE" or not operation.get("item_id"):
            return operation
        method_key = operation["method_key"]
        get_progress = self._get_progress_methods[method_key]
        operation_progress = get_progress(context, operation["item_id"])
        if operation_progress is None:
            return operation
        operation.update(operation_progress)
        if operation["progress"] == 100:
            operation["status"] = "DONE"
            operation["end_time"] = timeutils.isotime(None, True)
        self._update_db_item(context, operation)
        return operation

    def construct_operation(self, context, op_type, target_type, target_name,
                            scope):
        operation_id = str(uuid.uuid4())
        operation = {
            "id": operation_id,
            "name": "operation-" + operation_id,
            "insert_time": timeutils.isotime(context.timestamp, True),
            "user": context.user_name,
            "type": op_type,
            "target_type": target_type,
            "target_name": target_name,
            "scope_type": scope.get_type(),
            "scope_name": scope.get_name(),
        }
        return operation

    def save_operation(self, context, operation, start_time,
                       get_progress_method, item_id, operation_result):
        if isinstance(operation_result, Exception):
            operation.update(self._error_from_exception(operation_result))
        operation["start_time"] = start_time
        method_key = self._method_keys.get(get_progress_method)
        if method_key is None or "error_code" in operation:
            operation["progress"] = 100
            operation["status"] = "DONE"
            operation["end_time"] = timeutils.isotime(None, True)
        else:
            operation["progress"] = 0
            operation["status"] = "RUNNING"
            operation["method_key"] = method_key
            if item_id is not None:
                operation["item_id"] = item_id
        return self._add_db_item(context, operation)

    def update_operation(self, context, operation_id, operation_result):
        operation = self._get_db_item_by_id(context, operation_id)
        if operation is None:
            # NOTE(ft): it may lead to hungup not finished operation in DB
            return
        if isinstance(operation_result, Exception):
            operation.update(self._error_from_exception(operation_result))
        elif operation_result:
            operation.update(operation_result)
        if operation["progress"] == 100 or "error_code" in operation:
            operation["status"] = "DONE"
            operation["end_time"] = timeutils.isotime(None, True)
        self._update_db_item(context, operation)

    def _error_from_exception(self, ex):
        return {
            "errors": [{"code": ex.__class__.__name__, "message": str(ex)}],
            "error_code": 500,
            "error_message": _('Internal server error')}
