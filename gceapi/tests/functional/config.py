# Copyright 2012 OpenStack Foundation
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


from os import environ
from os import path
from oslo_config import cfg

from gceapi.tests.functional import config_opts


# This should never be called outside of this class
class ConfigPrivate(object):
    """Provides OpenStack configuration information."""

    def __init__(self):
        """Initialize a configuration from a conf directory and conf file."""
        super(ConfigPrivate, self).__init__()

        # if this was run from tempest runner then config already parsed
        if config_opts.gce_group.name in cfg.CONF:
            self.gce = cfg.CONF.gce
            return

        base_dir = self._get_base_dir()
        cfg_file_path = self._get_default_config_path(base_dir)
        config_files = []
        if path.exists(cfg_file_path):
            config_files.append(cfg_file_path)

        conf = cfg.CONF
        conf([], project='gceapi', default_config_files=config_files)
        conf.register_group(config_opts.OPTIONS_GROUP)
        group_name = config_opts.OPTIONS_GROUP.name
        for opt in config_opts.OPTIONS:
            conf.register_opt(opt, group=group_name)
        self.gce = cfg.CONF.gce
        conf.log_opt_values(LOG, std_logging.DEBUG)

        # Load API scheme for API calls validation
        with open(self._get_default_schema_path(base_dir), 'r') as f:
            from json import load
            self.gce.schema = load(f)

    @staticmethod
    def _get_base_dir():
        cur_dir = path.dirname(__file__)
        base_dir = path.dirname(path.dirname(path.dirname(cur_dir)))
        return environ.get('TEST_CONFIG_DIR', base_dir)

    @staticmethod
    def _get_default_config_path(base_dir):
        conf_file = environ.get('TEST_CONFIG', 'functional_tests.conf')
        return path.join(base_dir, conf_file)

    def _get_default_schema_path(self, base_dir):
        schema_file = environ.get('TEST_SCHEMA', self.gce.schema)
        return path.join(base_dir, schema_file)


class ConfigProxy(object):
    _config = None

    def __getattr__(self, attr):
        if not self._config:
            self._config = ConfigPrivate()

        return getattr(self._config, attr)


CONF = ConfigProxy()
