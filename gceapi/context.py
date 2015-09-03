# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack Foundation
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""RequestContext: context for requests that persist through all of gceapi."""

import uuid

from oslo_log import log as logging
from oslo_utils import timeutils

from gceapi import exception
from gceapi.i18n import _
from gceapi.openstack.common import local


LOG = logging.getLogger(__name__)


def generate_request_id():
    return 'req-' + str(uuid.uuid4())


class RequestContext(object):
    """Security context and request information.

    Represents the user taking a given action within the system.

    """

    def __init__(self, user_id, project_id, is_admin=None, read_deleted="no",
                 roles=None, remote_address=None, timestamp=None,
                 request_id=None, auth_token=None, overwrite=True,
                 user_name=None, project_name=None,
                 service_catalog=None, **kwargs):
        """
        :param read_deleted: 'no' indicates deleted records are hidden, 'yes'
            indicates deleted records are visible, 'only' indicates that
            *only* deleted records are visible.

        :param overwrite: Set to False to ensure that the greenthread local
            copy of the index is not overwritten.

        :param kwargs: Extra arguments that might be present, but we ignore
            because they possibly came in from older rpc messages.
        """
        if kwargs:
            LOG.warn(_('Arguments dropped when creating context: %s') %
                    str(kwargs))

        self.user_id = user_id
        self.project_id = project_id
        self.roles = roles or []
        self.read_deleted = read_deleted
        self.remote_address = remote_address
        if not timestamp:
            timestamp = timeutils.utcnow()
        if isinstance(timestamp, basestring):
            timestamp = timeutils.parse_strtime(timestamp)
        self.timestamp = timestamp
        if not request_id:
            request_id = generate_request_id()
        self.request_id = request_id
        self.auth_token = auth_token

        self.service_catalog = service_catalog

        self.user_name = user_name
        self.project_name = project_name
        self.is_admin = is_admin
        #if self.is_admin is None:
        #    self.is_admin = policy.check_is_admin(self)
        if overwrite or not hasattr(local.store, 'context'):
            self.update_store()
        self.operation = None
        self.operation_start_time = None
        self.operation_get_progress_method = None
        self.operation_item_id = None
        self.operation_data = {}

    def _get_read_deleted(self):
        return self._read_deleted

    def _set_read_deleted(self, read_deleted):
        if read_deleted not in ('no', 'yes', 'only'):
            raise ValueError(_("read_deleted can only be one of 'no', "
                               "'yes' or 'only', not %r") % read_deleted)
        self._read_deleted = read_deleted

    def _del_read_deleted(self):
        del self._read_deleted

    read_deleted = property(_get_read_deleted, _set_read_deleted,
                            _del_read_deleted)

    def update_store(self):
        local.store.context = self

    def to_dict(self):
        return {'user_id': self.user_id,
                'project_id': self.project_id,
                'is_admin': self.is_admin,
                'read_deleted': self.read_deleted,
                'roles': self.roles,
                'remote_address': self.remote_address,
                'timestamp': timeutils.strtime(self.timestamp),
                'request_id': self.request_id,
                'auth_token': self.auth_token,
                'user_name': self.user_name,
                'service_catalog': self.service_catalog,
                'project_name': self.project_name,
                'tenant': self.tenant,
                'user': self.user}

    @classmethod
    def from_dict(cls, values):
        return cls(**values)

    # NOTE(sirp): the openstack/common version of RequestContext uses
    # tenant/user whereas the gceapi version uses project_id/user_id. We need
    # this shim in order to use context-aware code from openstack/common, like
    # logging, until we make the switch to using openstack/common's version of
    # RequestContext.
    @property
    def tenant(self):
        return self.project_id

    @property
    def user(self):
        return self.user_id


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_admin:
        return False
    if not context.user_id or not context.project_id:
        return False
    return True


def require_context(ctxt):
    """Raise exception.NotAuthorized() if context is not a user or an
    admin context.
    """
    if not ctxt.is_admin and not is_user_context(ctxt):
        raise exception.NotAuthorized()
