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

from oslo_config import cfg

from gceapi.api import base_api
from gceapi.api import clients
from gceapi.api import operation_util
from gceapi.api import utils
from gceapi import exception

CONF = cfg.CONF


class API(base_api.API):
    """GCE Projects API."""

    KIND = "project"

    def _get_type(self):
        return self.KIND

    def get_item(self, context, name, scope=None):
        session = clients.admin_session()
        keystone = clients.keystone(context, session=session)
        project = keystone.projects.get(context.project_id)
        result = utils.to_dict(project)
        result["keypair"] = self._get_gce_keypair(context)
        project_id = project.id

        nova = clients.nova(context, session=session)
        nova_limits = nova.limits.get(tenant_id=project_id)
        result["nova_limits"] = dict((l.name, l.value)
                                     for l in nova_limits.absolute)

        cinder_client = clients.cinder(context, session=session)
        try:
            result["cinder_quotas"] = utils.to_dict(
                cinder_client.quotas.get(project_id, usage=True))
        except TypeError:
            # NOTE(apavlov): cinderclient of version 1.0.6 and below
            # has no usage parameter
            result["cinder_quotas"] = dict([("limit", x)
                for x in utils.to_dict(cinder_client.quotas.get(project_id))])

        net_api = CONF.get("network_api")
        if net_api is None or ("quantum" in net_api
                               or "neutron" in net_api):
            neutron_client = clients.neutron(context, session=session)
            result["neutron_quota"] = (
                neutron_client.show_quota(project_id)["quota"])
            result["neutron_quota"]["network_used"] = len(neutron_client
                .list_networks(tenant_id=project_id)["networks"])
            result["neutron_quota"]["floatingip_used"] = len(neutron_client
                .list_floatingips(tenant_id=project_id)["floatingips"])
            result["neutron_quota"]["security_group_used"] = len(neutron_client
                .list_security_groups(tenant_id=project_id)["security_groups"])
        else:
            result["neutron_quota"] = {}

        return result

    def get_items(self, context, scope=None):
        raise exception.NotFound

    def set_common_instance_metadata(self, context, metadata_list):
        instance_metadata = dict(
            [(x['key'], x['value']) for x in metadata_list])
        operation_util.start_operation(context)
        ssh_keys = instance_metadata.pop('sshKeys', None)
        if ssh_keys:
            nova_client = clients.nova(context)
            for key_data in ssh_keys.split('\n'):
                user_name, ssh_key = key_data.split(":")
                self._update_key(nova_client, user_name, ssh_key)

    def get_gce_user_keypair_name(self, context):
        client = clients.nova(context)
        for keypair in client.keypairs.list():
            if keypair.name == context.user_name:
                return keypair.name

        return None

    def _get_gce_keypair(self, context):
        client = clients.nova(context)
        key_datas = []
        for keypair in client.keypairs.list():
            key_datas.append(keypair.name + ':' + keypair.public_key)

        if not key_datas:
            return None

        return {'key': 'sshKeys', 'value': "\n".join(key_datas)}

    def _update_key(self, nova_client, user_name, ssh_key):
        try:
            keypair = nova_client.keypairs.get(user_name)
            if keypair.public_key == ssh_key:
                return

            keypair.delete()
        except clients.novaclient.exceptions.NotFound:
            pass

        keypair = nova_client.keypairs.create(user_name, ssh_key)
