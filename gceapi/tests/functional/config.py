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


OPTIONS_GROUP = cfg.OptGroup(name='gce', title='GCE options')
OPTIONS = [
    # Generic options
    cfg.IntOpt('build_timeout',
               default=180,
               help='Timeout'),
    cfg.IntOpt('build_interval',
               default=1,
               help='Interval'),

    # GCE API schema
    cfg.StrOpt('schema',
               default='etc/gceapi/protocols/v1.json',
               help='Json file with API schema for validation'),

    # GCE services address
    cfg.StrOpt('protocol',
               default='http',
               help='GCE protocl (http or https)'),
    cfg.StrOpt('host',
               default='localhost',
               help='GCE service host'),
    cfg.IntOpt('port',
               default=8787,
               help='GCE service port'),

    # GCE URLs
    cfg.StrOpt('auth_url',
               default='/auth',
               help='OAuth API relative URL'),
    cfg.StrOpt('discovery_url',
               default='/discovery/v1/apis/{api}/{apiVersion}/rest',
               help='Discovery API relative URL'),

    # GCE resource IDs for testing
    cfg.StrOpt('project_id',
               default='test',
               help='GCE Project ID for testing'),
    cfg.StrOpt('zone',
               default='nova',
               help='GCE Zone for testing'),
    cfg.StrOpt('region',
               default='RegionOne',
               help='GCE Region for testing'),
]


# This should never be called outside of this class
class ConfigPrivate(object):
    """Provides OpenStack configuration information."""

    def __init__(self):
        """Initialize a configuration from a conf directory and conf file."""
        super(ConfigPrivate, self).__init__()
        base_dir = self._get_base_dir()
        cfg_file_path = self._get_default_config_path(base_dir)
        config_files = []
        if path.exists(cfg_file_path):
            config_files.append(cfg_file_path)
        cfg.CONF.register_group(OPTIONS_GROUP)
        cfg.CONF.register_opts(OPTIONS, group=OPTIONS_GROUP)
        cfg.CONF([], project='gceapi', default_config_files=config_files)
        self.gce = cfg.CONF.gce
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
