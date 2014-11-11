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

from gceapi.api import base_api
from gceapi.api import route_neutron_api
from gceapi.api import route_nova_api


class API(base_api.API):
    """GCE Route API."""

    NEUTRON_API_MODULE = route_neutron_api
    NOVA_API_MODULE = route_nova_api

    __metaclass__ = base_api.NetSingleton
