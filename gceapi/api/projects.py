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

import webob

from gceapi import exception

from gceapi.api import common as gce_common
from gceapi.api import operation_util
from gceapi.api import project_api
from gceapi.api import scopes
from gceapi.api import wsgi as gce_wsgi
from gceapi.i18n import _


class Controller(gce_common.Controller):
    """GCE Projects controller"""

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(project_api.API(), *args, **kwargs)

    def format_item(self, request, project, scope):
        desc = project["description"]
        result_dict = {
            "name": project["name"],
            "description": desc if desc else "",
            "commonInstanceMetadata": {
                "kind": "compute#metadata",
                "items": [project["keypair"]]
            } if project["keypair"] else {
                "kind": "compute#metadata",
            },
            "quotas": []
        }

        self._add_quota(result_dict["quotas"], "CPUS",
            project["nova_limits"].get("maxTotalCores", -1),
            project["nova_limits"].get("totalCoresUsed", -1))
        self._add_quota(result_dict["quotas"], "INSTANCES",
            project["nova_limits"].get("maxTotalInstances", -1),
            project["nova_limits"].get("totalInstancesUsed", -1))

        quota = project["cinder_quotas"].get("gigabytes", {})
        self._add_quota(result_dict["quotas"], "DISKS_TOTAL_GB",
            quota.get("limit", -1), quota.get("in_use", -1))
        quota = project["cinder_quotas"].get("snapshots", {})
        self._add_quota(result_dict["quotas"], "SNAPSHOTS",
            quota.get("limit", -1), quota.get("in_use", -1))
        quota = project["cinder_quotas"].get("volumes", {})
        # Note(alexey-mr): GCE has no limit by number of disks
        # self._add_quota(result_dict["quotas"], "DISKS",
        #     quota.get("limit", -1), quota.get("in_use", -1))

        self._add_quota(result_dict["quotas"], "FIREWALLS",
            project["neutron_quota"].get("security_group", -1),
            project["neutron_quota"].get("security_group_used", -1))
        self._add_quota(result_dict["quotas"], "STATIC_ADDRESSES",
            project["neutron_quota"].get("floatingip", -1),
            project["neutron_quota"].get("floatingip_used", -1))
        self._add_quota(result_dict["quotas"], "NETWORKS",
            project["neutron_quota"].get("network", -1),
            project["neutron_quota"].get("network_used", -1))

        return self._format_item(request, result_dict, scope)

    def set_common_instance_metadata(self, req, body):
        context = self._get_context(req)
        operation_util.init_operation(context, "setMetadata", self._type_name,
                                      None, scopes.GlobalScope())
        try:
            self._api.set_common_instance_metadata(
                context, body.get("items", []))
        except exception.KeypairLimitExceeded:
            msg = _("Quota exceeded, too many key pairs.")
            raise webob.exc.HTTPRequestEntityTooLarge(
                        explanation=msg,
                        headers={'Retry-After': 0})
        except exception.InvalidKeypair:
            msg = _("Keypair data is invalid")
            raise webob.exc.HTTPBadRequest(explanation=msg)
        except exception.KeyPairExists:
            msg = _("Key pair already exists.")
            raise webob.exc.HTTPConflict(explanation=msg)

    def _add_quota(self, quotas, metric, limit, usage):
        quotas.append({
            "metric": metric,
            "limit": float(limit),
            "usage": float(usage),
        })


def create_resource():
    return gce_wsgi.GCEResource(Controller())
