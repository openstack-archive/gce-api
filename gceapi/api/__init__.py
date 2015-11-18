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
from oslo_log import log as logging

from gceapi.api import addresses
from gceapi.api import discovery
from gceapi.api import disks
from gceapi.api import firewalls
from gceapi.api import images
from gceapi.api import instances
from gceapi.api import machine_types
from gceapi.api import networks
from gceapi.api import oauth
from gceapi.api import operations
from gceapi.api import projects
from gceapi.api import regions
from gceapi.api import routes
from gceapi.api import snapshots
from gceapi.api import zones
from gceapi import wsgi
from gceapi import wsgi_ext as openstack_api

LOG = logging.getLogger(__name__)


gce_opts = [
    cfg.StrOpt('network_api',
        default="neutron",
        help='Name of network API. neutron(quantum) or nova'),
    cfg.StrOpt('keystone_url',
        default='http://127.0.0.1:5000/v2.0',
        help='Keystone URL'),
    cfg.StrOpt('public_network',
        default='public',
        help='name of public network'),
    cfg.StrOpt('protocol_dir',
        default=None,
        help='Place of protocol files'),
    cfg.StrOpt('region',
        default='RegionOne',
        help='Region of this service'),
    cfg.IntOpt('default_volume_size_gb',
        default=500,
        help='Default new volume size if sizeGb, sourceSnapshot and '
             'sourceImage are not provided'),
    cfg.StrOpt('default_network_name',
        default='default',
        help='Default network name that expected to exists'),
    cfg.StrOpt('default_network_ip_range',
        default='10.240.0.0/16',
        help='Default new network ip range if it is not provided'),
    ]

CONF = cfg.CONF
CONF.register_opts(gce_opts)


class APIRouter(wsgi.Router):
    """
    Routes requests on the GCE API to the appropriate controller
    and method.
    """

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, `gceapi.wsgi.Router` doesn't have one."""

        return cls()

    def __init__(self):
        mapper = openstack_api.ProjectMapper()
        self.resources = {}
        self._setup_routes(mapper)
        super(APIRouter, self).__init__(mapper)

    def _setup_routes(self, mapper):
        mapper.redirect("", "/")

        self.resources['regions'] = regions.create_resource()
        self.resources['firewalls'] = firewalls.create_resource()
        self.resources['disks'] = disks.create_resource()
        self.resources['machineTypes'] = machine_types.create_resource()
        self.resources['instances'] = instances.create_resource()
        self.resources['images'] = images.create_resource()
        self.resources['instances'] = instances.create_resource()
        self.resources['zones'] = zones.create_resource()
        self.resources['networks'] = networks.create_resource()
        self.resources['instances'] = instances.create_resource()
        self.resources['projects'] = projects.create_resource()
        self.resources['snapshots'] = snapshots.create_resource()
        self.resources['addresses'] = addresses.create_resource()
        self.resources['routes'] = routes.create_resource()
        self.resources['operations'] = operations.create_resource()

        mapper.resource("disks", "zones/{scope_id}/disks",
                controller=self.resources['disks'])
        mapper.connect("/{project_id}/aggregated/disks",
                controller=self.resources['disks'],
                action="aggregated_list",
                conditions={"method": ["GET"]})
        mapper.connect("/{project_id}/zones/{scope_id}/disks/{id}/"
                       "createSnapshot",
                controller=self.resources['disks'],
                action="create_snapshot",
                conditions={"method": ["POST"]})

        mapper.resource("machineTypes", "zones/{scope_id}/machineTypes",
                controller=self.resources['machineTypes'])
        mapper.connect("/{project_id}/aggregated/machineTypes",
                controller=self.resources['machineTypes'],
                action="aggregated_list",
                conditions={"method": ["GET"]})

        mapper.resource("instances", "zones/{scope_id}/instances",
                controller=self.resources['instances'])
        mapper.connect("/{project_id}/aggregated/instances",
                controller=self.resources['instances'],
                action="aggregated_list",
                conditions={"method": ["GET"]})
        mapper.connect("/{project_id}/zones/{scope_id}/instances/{id}/"
                       "addAccessConfig",
                controller=self.resources['instances'],
                action="add_access_config",
                conditions={"method": ["POST"]})
        mapper.connect("/{project_id}/zones/{scope_id}/instances/{id}/"
                       "deleteAccessConfig",
                controller=self.resources['instances'],
                action="delete_access_config",
                conditions={"method": ["POST"]})
        mapper.connect("/{project_id}/zones/{scope_id}/instances/{id}/reset",
                controller=self.resources['instances'],
                action="reset_instance",
                conditions={"method": ["POST"]})
        mapper.connect("/{project_id}/zones/{scope_id}/instances/{id}/"
                       "attachDisk",
                controller=self.resources['instances'],
                action="attach_disk",
                conditions={"method": ["POST"]})
        mapper.connect("/{project_id}/zones/{scope_id}/instances/{id}/"
                       "detachDisk",
                controller=self.resources['instances'],
                action="detach_disk",
                conditions={"method": ["POST"]})
        mapper.connect("/{project_id}/zones/{scope_id}/instances/{id}/"
                       "setDiskAutoDelete",
                controller=self.resources['instances'],
                action="set_disk_auto_delete",
                conditions={"method": ["POST"]})

        mapper.resource("images", "global/images",
                controller=self.resources['images'])
        mapper.resource("regions", "regions",
                controller=self.resources['regions'])
        mapper.resource("zones", "zones",
                controller=self.resources['zones'])
        mapper.resource("networks", "global/networks",
                controller=self.resources["networks"])
        mapper.resource("firewalls", "global/firewalls",
                controller=self.resources["firewalls"])
        mapper.resource("routes", "global/routes",
                controller=self.resources['routes'])

        mapper.connect("/{project_id}", controller=self.resources['projects'],
                action="show", conditions={"method": ["GET"]})
        mapper.connect("/{project_id}/setCommonInstanceMetadata",
                controller=self.resources['projects'],
                action="set_common_instance_metadata",
                conditions={"method": ["POST"]})

        mapper.resource("addresses", "regions/{scope_id}/addresses",
                controller=self.resources['addresses'])
        mapper.connect("/{project_id}/aggregated/addresses",
                controller=self.resources['addresses'],
                action="aggregated_list",
                conditions={"method": ["GET"]})

        mapper.resource("snapshots", "global/snapshots",
                controller=self.resources['snapshots'])

        mapper.resource("operations", "global/operations",
                controller=self.resources['operations'])
        mapper.resource("operations", "regions/{scope_id}/operations",
                controller=self.resources['operations'])
        mapper.resource("operations", "zones/{scope_id}/operations",
                controller=self.resources['operations'])
        mapper.connect("/{project_id}/aggregated/operations",
                controller=self.resources['operations'],
                action="aggregated_list",
                conditions={"method": ["GET"]})


class APIRouterOAuth(wsgi.Router):
    """
    Routes requests on the OAuth2.0 to the appropriate controller
    and method.
    """

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, `gceapi.wsgi.Router` doesn't have one."""

        return cls()

    def __init__(self):
        mapper = openstack_api.ProjectMapper()
        self.resources = {}
        self._setup_routes(mapper)
        super(APIRouterOAuth, self).__init__(mapper)

    def _setup_routes(self, mapper):
        mapper.redirect("", "/")

        self.resources['oauth'] = oauth.create_resource()

        mapper.connect("/auth",
            controller=self.resources['oauth'],
            action="auth",
            conditions={"method": ["GET"]})
        mapper.connect("/approval",
            controller=self.resources['oauth'],
            action="approval",
            conditions={"method": ["POST"]})
        mapper.connect("/token",
            controller=self.resources['oauth'],
            action="token",
            conditions={"method": ["POST"]})


class APIRouterDiscovery(wsgi.Router):
    """
    Routes requests on the GCE discovery API to the appropriate controller
    and method.
    """

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, `gceapi.wsgi.Router` doesn't have one."""

        return cls()

    def __init__(self):
        mapper = openstack_api.ProjectMapper()
        self.resources = {}
        self._setup_routes(mapper)
        super(APIRouterDiscovery, self).__init__(mapper)

    def _setup_routes(self, mapper):
        mapper.redirect("", "/")

        self.resources['discovery'] = discovery.create_resource()

        mapper.connect("/{version}/rest",
                controller=self.resources['discovery'],
                action="discovery",
                conditions={"method": ["GET"]})
