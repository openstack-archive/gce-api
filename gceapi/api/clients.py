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

from keystoneclient.auth import identity as keystone_identity
from keystoneclient import client as keystone_client
from keystoneclient import session as keystone_session

from novaclient import client as novaclient
from novaclient import exceptions as nova_exception
from oslo_config import cfg
from oslo_log import log as logging

from gceapi.i18n import _, _LW

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


def admin_session():
    auth = keystone_identity.Password(
        auth_url=CONF.keystone_url,
        username=CONF.keystone_authtoken['admin_user'],
        password=CONF.keystone_authtoken['admin_password'],
        project_name=CONF.keystone_authtoken['admin_tenant_name'])
    session = keystone_session.Session(auth=auth)
    return session


def create_session_for_context(context):
    auth = keystone_identity.Token(
        auth_url=CONF.keystone_url,
        token=context.auth_token,
        project_id=context.project_id
    )
    session = keystone_session.Session(auth=auth)
    return session


def nova(context, service_type='compute', session=None):
    s = session if session else create_session_for_context(context)
    args = {
        'session': s,
        'bypass_url': url_for(context, service_type),
    }
    global _nova_api_version
    if not _nova_api_version:
        _nova_api_version = _get_nova_api_version(context)
    return novaclient.Client(_nova_api_version, **args)


def neutron(context, session=None):
    if neutronclient is None:
        return None
    s = session if session else create_session_for_context(context)
    args = {
        'session': s,
        'service_type': 'network',
        'endpoint_url': url_for(context, 'network'),
    }
    return neutronclient.Client(**args)


def glance(context, session=None):
    if glanceclient is None:
        return None
    s = session if session else create_session_for_context(context)
    args = {
        'session': s,
        'service_type': 'image',
        'endpoint': url_for(context, 'image')
    }
    return glanceclient.Client("1", **args)


def cinder(context, session=None):
    if cinderclient is None:
        return nova(context, 'volume', session=session)
    s = session if session else create_session_for_context(context)
    args = {
        'session': s,
        'service_type': 'volume',
        'username': None,
        'api_key': None,
    }
    _cinder = cinderclient.Client('1', **args)
    management_url = url_for(context, 'volume')
    _cinder.client.auth_token = context.auth_token
    _cinder.client.management_url = management_url
    return _cinder


def keystone(context, session=None):
    s = session if session else create_session_for_context(context)
    client = keystone_client.Client(
        session=s,
        auth_url=CONF.keystone_url
    )
    return client


def url_for(context, service_type):
    service_catalog = context.service_catalog
    if not service_catalog:
        service_catalog = keystone(context).service_catalog.get_data()
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
