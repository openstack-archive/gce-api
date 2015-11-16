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

from gceapi.tests.unit.api import fake_request
from gceapi.tests.unit.api import utils


FAKE_PROJECTS = [utils.FakeObject({
    "name": "fake_project",
    "description": None,
    "id": fake_request.PROJECT_ID,
    "enabled": True
})]


class FakeProjects(object):
    def list(self):
        return FAKE_PROJECTS

    def get(self, project_id):
        return FAKE_PROJECTS[0]


class FakeAccessInfo(object):
    pass


class FakeKeystoneClient(object):
    def __init__(self, **kwargs):
        pass

    @property
    def projects(self):
        return FakeProjects()

    @property
    def auth_ref(self):
        return FakeAccessInfo()


class FakePassword(object):
    def __init__(self, **kwargs):
        pass
