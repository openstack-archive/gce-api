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
from oslo_config import cfg
from oslo_log import log as logging

from gceapi import context as gce_context
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


# Nova API version with microversions support
REQUIRED_NOVA_API_VERSION = '2.1'
LEGACY_NOVA_API_VERSION = '2'
# Nova API's 2.3 microversion provides additional EC2 compliant instance
# properties
REQUIRED_NOVA_API_MICROVERSION = '2.3'
_nova_api_version = None


def nova(context, service_type='compute'):
    args = {
        'auth_url': CONF.keystone_gce_url,
        'auth_token': context.auth_token,
        'bypass_url': url_for(context, service_type),
    }
    global _nova_api_version
    if not _nova_api_version:
        _nova_api_version = _get_nova_api_version(context)
    return novaclient.Client(_nova_api_version, **args)


def neutron(context):
    if neutronclient is None:
        return None

    args = {
        'auth_url': CONF.keystone_gce_url,
        'service_type': 'network',
        'token': context.auth_token,
        'endpoint_url': url_for(context, 'network'),
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
        "1", endpoint=url_for(context, 'image'), **args)


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
    management_url = url_for(context, 'volume')
    _cinder.client.auth_token = context.auth_token
    _cinder.client.management_url = management_url

    return _cinder


def keystone(context):
    return kc.Client(
        token=context.auth_token,
        project_id=context.project_id,
        tenant_id=context.project_id,
        auth_url=CONF.keystone_gce_url)


def url_for(context, service_type):
    service_catalog = context.service_catalog
    if not service_catalog:
        catalog = keystone(context).service_catalog.catalog
        service_catalog = catalog['serviceCatalog']
        context.service_catalog = service_catalog
    return get_url_from_catalog(service_catalog, service_type)


def get_url_from_catalog(service_catalog, service_type):
    for service in service_catalog:
        if service['type'] != service_type:
            continue
        for endpoint in service['endpoints']:
            if 'publicURL' in endpoint:
                return endpoint['publicURL']
            elif endpoint.get('interface') == 'public':
                # NOTE(andrey-mp): keystone v3
                return endpoint['url']
        else:
            return None

    return None


def _get_nova_api_version(context):
    try:
        novaclient.Client(REQUIRED_NOVA_API_VERSION)
    except nova_exception.UnsupportedVersion:
        logger.warning(
            _LW('Nova client does not support v2.1 Nova API, use v2 instead. '
                'A lot of useful EC2 compliant instance properties '
                'will be unavailable.'))
        return LEGACY_NOVA_API_VERSION

    # NOTE(ft): novaclient supports microversions, use the last required one
    return REQUIRED_NOVA_API_MICROVERSION

