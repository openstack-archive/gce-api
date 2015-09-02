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

import threading

from oslo_utils import timeutils

from gceapi.api import operation_api
from gceapi.i18n import _


def init_operation(context, op_type, target_type, target_name, scope):
    if context.operation is not None:
        return
    operation = operation_api.API().construct_operation(
            context, op_type, target_type, target_name, scope)
    context.operation = operation
    return operation


def save_operation(context, action_result):
    if context.operation is None or context.operation_start_time is None:
        return None
    return operation_api.API().save_operation(
            context,
            context.operation,
            context.operation_start_time,
            context.operation_get_progress_method,
            context.operation_item_id,
            action_result)


def start_operation(context, get_progress_method=None, item_id=None):
    if context.operation is None or context.operation_start_time is not None:
        return
    context.operation_start_time = timeutils.isotime(None, True)
    context.operation_get_progress_method = get_progress_method
    context.operation_item_id = item_id


def set_item_id(context, item_id, item_type):
    if (context.operation is None
            or context.operation_start_time is None
            or context.operation["target_type"] != item_type):
        return
    context.operation_item_id = item_id


def continue_operation(context, func, timeout=5):
    threading.Timer(timeout, _continue_operation, [context, func]).start()


def _continue_operation(context, func):
    operation = context.operation
    try:
        operation_result = func()
        if not is_final_progress(operation_result):
            continue_operation(context, func, timeout=2)
    except Exception as ex:
        operation_result = ex

    operation_api.API().update_operation(context, operation["id"],
                                         operation_result)


def get_final_progress(with_error=False):
    progress = {"progress": 100}
    if with_error:
        progress["error_code"] = 500
        progress["error_message"] = _('Internal server error')
        progress["errors"] = [{
           "code": "UNKNOWN_OS_ERROR",
           "message": _("Operation finished with unknown error. "
                        "See OpenStack logs.")
        }]
    return progress


def is_final_progress(progress):
    return progress is not None and (progress.get("progress") == 100 or
                                     progress.get("error_code") is not None)
