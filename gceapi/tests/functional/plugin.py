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

import os

from tempest import config
from tempest.test_discover import plugins

from gceapi.tests.functional import config_opts as gce_config


class GCETempestPlugin(plugins.TempestPlugin):
    def load_tests(self):
        base_path = os.path.split(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))[0]
        test_dir = "gceapi/tests/functional"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        if gce_config.gce_group.name not in conf:
            config.register_opt_group(conf, gce_config.gce_group,
                                      gce_config.GCEGroup)

    def get_opt_lists(self):
        return [(gce_config.gce_group.name, config.GCEGroup)]
