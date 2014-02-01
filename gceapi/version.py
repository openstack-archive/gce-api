# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Copyright 2011 OpenStack Foundation
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

import pbr.version

GCEAPI_VENDOR = "OpenStack Foundation"
GCEAPI_PRODUCT = "OpenStack Gceapi"
GCEAPI_PACKAGE = None  # OS distro package version suffix

loaded = False
version_info = pbr.version.VersionInfo('gceapi')
version_string = version_info.version_string


def _load_config():
    # Don't load in global context, since we can't assume
    # these modules are accessible when distutils uses
    # this module
    import ConfigParser

    from oslo.config import cfg

    from gceapi.openstack.common import log as logging

    global loaded, GCEAPI_VENDOR, GCEAPI_PRODUCT, GCEAPI_PACKAGE
    if loaded:
        return

    loaded = True

    cfgfile = cfg.CONF.find_file("release")
    if cfgfile is None:
        return

    try:
        cfg = ConfigParser.RawConfigParser()
        cfg.read(cfgfile)

        GCEAPI_VENDOR = cfg.get("Gceapi", "vendor")
        if cfg.has_option("Gceapi", "vendor"):
            GCEAPI_VENDOR = cfg.get("Gceapi", "vendor")

        GCEAPI_PRODUCT = cfg.get("Gceapi", "product")
        if cfg.has_option("Gceapi", "product"):
            GCEAPI_PRODUCT = cfg.get("Gceapi", "product")

        GCEAPI_PACKAGE = cfg.get("Gceapi", "package")
        if cfg.has_option("Gceapi", "package"):
            GCEAPI_PACKAGE = cfg.get("Gceapi", "package")
    except Exception as ex:
        LOG = logging.getLogger(__name__)
        LOG.error("Failed to load %(cfgfile)s: %(ex)s",
                  {'cfgfile': cfgfile, 'ex': ex})


def vendor_string():
    _load_config()

    return GCEAPI_VENDOR


def product_string():
    _load_config()

    return GCEAPI_PRODUCT


def package_string():
    _load_config()

    return GCEAPI_PACKAGE


def version_string_with_package():
    if package_string() is None:
        return version_info.version_string()
    else:
        return "%s-%s" % (version_info.version_string(), package_string())
