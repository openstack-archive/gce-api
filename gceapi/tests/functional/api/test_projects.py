# Copyright 2015 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

import copy

from gceapi.tests.functional.api import test_instances


class TestProjects(test_instances.TestInstancesBase):
    @property
    def projects(self):
        res = self.api.compute.projects()
        self.assertIsNotNone(
            res,
            'Null projects object, api is not built properly')
        return res

    def _get_project(self):
        project_id = self.cfg.project_id
        self.trace('Get project: project_id={}'.format(project_id))
        request = self.projects.get(project=project_id)
        result = request.execute()
        self.trace('Project: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Project')
        return result

    def _set_common_metadata(self, options):
        cfg = self.cfg
        project_id = cfg.project_id
        self.trace('Set common metadata options {}'.format(options))
        request = self.projects.setCommonInstanceMetadata(
            project=project_id,
            body=options)
        self._execute_async_request(request, project_id)

    @staticmethod
    def _get_expected_common_metadata(options):
        meta = copy.deepcopy(options)
        meta.setdefault('kind', 'compute#metadata')
        meta.setdefault('fingerprint', '.*')
        return meta

    def _get_expected_project(self, options):
        project = copy.deepcopy(options)
        name = project['name']
        project.setdefault('kind', 'compute#project')
        project.setdefault('selfLink', self.api.get_global_url(name))
        project.setdefault('quotas', [])
        expected_common_meta = self._get_expected_common_metadata(
            project.get('commonInstanceMetadata', dict()))
        project['commonInstanceMetadata'] = expected_common_meta
        project.setdefault('id', '[0-9]+')
        project.setdefault('creationTimestamp', '.*')
        return project

    def test_get_project(self):
        project = self._get_project()
        options = {'name': self.cfg.project_id}
        expected_project = self._get_expected_project(options)
        self.assertObject(expected_project, project)

    def test_set_common_metadata(self):
        # save current project metadata
        before_test_state = self._get_project()
        before_test_metadata = before_test_state['commonInstanceMetadata']
        before_test_metadata.pop('kind')
        before_test_metadata.pop('fingerprint')
        self._add_cleanup(self._set_common_metadata, before_test_metadata)
        # do test
        metadata = {
            'items': [
                {
                    'key': self._rand_name('test-metadata-key'),
                    'value': self._rand_name('test-metadata-value')
                }
            ]
        }
        self._set_common_metadata(metadata)
        project = self._get_project()
        expected_project = {
            'name': self.cfg.project_id,
            'commonInstanceMetadata': metadata
        }
        expected_project = self._get_expected_project(expected_project)
        self.assertObject(expected_project, project)
        # return previous state
        self._set_common_metadata(before_test_metadata)
        self._remove_cleanup(self._set_common_metadata, before_test_metadata)
        project = self._get_project()
        self.assertObject(before_test_state, project)
