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

from oslo_log import log as logging

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import operation_util
from gceapi import exception
from gceapi.i18n import _

LOG = logging.getLogger(__name__)


class API(base_api.API):
    """GCE Access config API."""

    KIND = "access_config"
    PERSISTENT_ATTRIBUTES = ["id", "instance_name",
                             "nic", "name", "type", "addr"]
    DEFAULT_ACCESS_CONFIG_TYPE = "ONE_TO_ONE_NAT"
    DEFAULT_ACCESS_CONFIG_NAME = "External NAT"

    def __init__(self, *args, **kwargs):
        super(API, self).__init__(*args, **kwargs)

    def _get_type(self):
        return self.KIND

    def _get_persistent_attributes(self):
        return self.PERSISTENT_ATTRIBUTES

    def get_item(self, context, instance_name, name):
        items = self._get_db_items(context)
        items = [i for i in items
                if i["instance_name"] == instance_name and i["name"] == name]
        if len(items) != 1:
            raise exception.NotFound
        return items[0]

    def get_items(self, context, instance_name):
        items = self._get_db_items(context)
        return [i for i in items if i["instance_name"] == instance_name]

    def add_item(self, context, instance_name, nic, addr, addr_type, name):
        if not nic:
            msg = _("Network interface is invalid or empty")
            raise exception.InvalidRequest(msg)

        if addr_type is None:
            addr_type = self.DEFAULT_ACCESS_CONFIG_TYPE
        elif addr_type != self.DEFAULT_ACCESS_CONFIG_TYPE:
            msg = _("Only '%s' type of access config currently supported.")\
                    % self.DEFAULT_ACCESS_CONFIG_TYPE
            raise exception.InvalidRequest(msg)

        client = clients.nova(context)
        instances = client.servers.list(search_opts={"name": instance_name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]

        fixed_ip = None
        for network in instance.addresses:
            if nic != network:
                continue
            for address in instance.addresses[network]:
                atype = address["OS-EXT-IPS:type"]
                if atype == "floating":
                    msg = _('At most one access config currently supported.')
                    raise exception.InvalidRequest(msg)
                if atype == "fixed":
                    fixed_ip = address["addr"]

        if not fixed_ip:
            msg = _('Network interface not found')
            raise exception.InvalidRequest(msg)

        floating_ips = client.floating_ips.list()
        if addr is None:
            # NOTE(apavlov): try to find unused
            for floating_ip in floating_ips:
                if floating_ip.instance_id is None:
                    addr = floating_ip.ip
                    break
            else:
                msg = _('There is no unused floating ips.')
                raise exception.InvalidRequest(msg)
        else:
            for floating_ip in floating_ips:
                if floating_ip.ip != addr:
                    continue
                if floating_ip.instance_id is None:
                    break
                msg = _("Floating ip '%s' is already associated") % floating_ip
                raise exception.InvalidRequest(msg)
            else:
                msg = _("There is no such floating ip '%s'.") % addr
                raise exception.InvalidRequest(msg)

        operation_util.start_operation(context)
        instance.add_floating_ip(addr, fixed_ip)

        return self.register_item(context, instance_name,
                                  nic, addr, addr_type, name)

    def register_item(self, context, instance_name,
                      nic, addr, addr_type, name):
        if not nic:
            msg = _("Network interface is invalid or empty")
            raise exception.InvalidRequest(msg)

        if addr_type is None:
            addr_type = self.DEFAULT_ACCESS_CONFIG_TYPE
        elif addr_type != self.DEFAULT_ACCESS_CONFIG_TYPE:
            msg = _("Only '%s' type of access config currently supported.")\
                % self.DEFAULT_ACCESS_CONFIG_TYPE
            raise exception.InvalidRequest(msg)

        if name is None:
            name = self.DEFAULT_ACCESS_CONFIG_NAME
        if not addr:
            msg = _("There is no address to assign.")
            raise exception.InvalidRequest(msg)

        new_item = {
            "id": instance_name + "-" + addr,
            "instance_name": instance_name,
            "nic": nic,
            "name": name,
            "type": addr_type,
            "addr": addr
        }
        new_item = self._add_db_item(context, new_item)
        return new_item

    def delete_item(self, context, instance_name, name):
        client = clients.nova(context)
        instances = client.servers.list(search_opts={"name": instance_name})
        if not instances or len(instances) != 1:
            raise exception.NotFound
        instance = instances[0]

        item = self.get_item(context, instance_name, name)
        floating_ip = item["addr"]
        operation_util.start_operation(context)
        instance.remove_floating_ip(floating_ip)
        self._delete_db_item(context, item)

    def unregister_item(self, context, instance_name, name):
        item = self.get_item(context, instance_name, name)
        self._delete_db_item(context, item)
