# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from keystoneclient.v2_0 import client as kc
from novaclient import client as novaclient
from novaclient import shell as novashell
from oslo_config import cfg
from oslo_log import log as logging

from gceapi.i18n import _

logger = logging.getLogger(__name__)

CONF = cfg.CONF


try:
    from neutronclient.v2_0 import client as neutronclient
except ImportError:
    neutronclient = None
    logger.info(_('neutronclient not available'))
try:
    from cinderclient import client as cinderclient
except ImportError:
    cinderclient = None
    logger.info(_('cinderclient not available'))
try:
    from glanceclient import client as glanceclient
except ImportError:
    glanceclient = None
    logger.info(_('glanceclient not available'))


def nova(context, service_type='compute'):
    computeshell = novashell.OpenStackComputeShell()
    extensions = computeshell._discover_extensions("1.1")

    args = {
        'project_id': context.project_id,
        'auth_url': CONF.keystone_gce_url,
        'service_type': service_type,
        'username': None,
        'api_key': None,
        'extensions': extensions,
    }

    client = novaclient.Client(1.1, **args)

    management_url = get_endpoint(context, service_type)
    client.client.auth_token = context.auth_token
    client.client.management_url = management_url

    return client


def neutron(context):
    if neutronclient is None:
        return None

    args = {
        'auth_url': CONF.keystone_gce_url,
        'service_type': 'network',
        'token': context.auth_token,
        'endpoint_url': get_endpoint(context, 'network'),
    }

    return neutronclient.Client(**args)


def glance(context):
    if glanceclient is None:
        return None

    args = {
        'auth_url': CONF.keystone_gce_url,
        'service_type': 'image',
        'token': context.auth_token,
    }

    return glanceclient.Client(
        "1", endpoint=get_endpoint(context, 'image'), **args)


def cinder(context):
    if cinderclient is None:
        return nova(context, 'volume')

    args = {
        'service_type': 'volume',
        'auth_url': CONF.keystone_gce_url,
        'username': None,
        'api_key': None,
    }

    _cinder = cinderclient.Client('1', **args)
    management_url = get_endpoint(context, 'volume')
    _cinder.client.auth_token = context.auth_token
    _cinder.client.management_url = management_url

    return _cinder


def keystone(context):
    _keystone = kc.Client(
        token=context.auth_token,
        tenant_id=context.project_id,
        auth_url=CONF.keystone_gce_url)

    return _keystone


def get_endpoint_from_catalog(service_catalog, service_type):
    for service in service_catalog:
        if service["type"] != service_type:
            continue
        for endpoint in service["endpoints"]:
            if endpoint["region"] != CONF["region"]:
                continue
            return endpoint.get("publicURL")

        return None

    return None


def get_endpoint(context, service_type):
    service_catalog = context.service_catalog
    if not service_catalog:
        catalog = keystone(context).service_catalog.catalog
        service_catalog = catalog["serviceCatalog"]
        context.service_catalog = service_catalog

    return get_endpoint_from_catalog(service_catalog, service_type)
