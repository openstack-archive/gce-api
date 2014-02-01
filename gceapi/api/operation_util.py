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

import threading

from gceapi.api import operation_api
from gceapi.openstack.common import timeutils


def init_operation(context, op_type, target_type, target_name, scope):
    if context.operation is not None:
        return
    operation = operation_api.API().construct_operation(
            context, op_type, target_type, target_name, scope)
    context.operation = operation
    return operation


def save_operaton(context, action_result):
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
    set_item_id(context, item_id)


def set_item_id(context, item_id):
    if context.operation is None or context.operation_start_time is None:
        return
    context.operation_item_id = item_id


def continue_operation(context, func, timeout=5):
    threading.Timer(timeout, _continue_operation, [context, func]).start()


def _continue_operation(context, func):
    operation = context.operation
    try:
        operation_result = func()
    except Exception as ex:
        operation_result = ex
    if operation is None:
        return
    if operation_result is None:
        continue_operation(context, func, timeout=2)
    else:
        operation_api.API().update_operation(context, operation["id"],
                                             operation_result)
