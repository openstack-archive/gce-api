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

from gceapi.tests.functional import test_base

from gceapi.tests.functional.api import test_instances


SSH_KEY = ('testuser:ssh-rsa '
           'AAAAB3NzaC1yc2EAAAADAQABAAACAQDhxWFq3wWIW8QSJsbTFT9x+eSvOt5jAs'
           'UDBW15DUU2l5Qh1E/DXtv4NnwiI7RDquBI0YAtEcNN1mYwZWNwNs+VSW39YJCS'
           'RhUQ/WQA3bp3jrTqi8uitNnAW1EprGFAxcQHQV0g64WC/8/Ou6VYMV8ChaNPjN'
           'mY1Yzy6maGJDizYLbJ/tMnfNBQoMF2HTKPhC9edtR2ZQT6SY9wcI1xFk6+pqQt'
           '69sGAYA3xoleqGRFwxi0xwMKmyKIZ7Uvp7jH6vJraTGIJmhfU4ueZKWBzwFcKM'
           'XBZbpBR4lvxHrYX8W4BqMbvFvVkX41pzvlc0gmCW/F3Iyoldqfb9pt+72/zaht'
           'yw7sIKeSJaTl0WlHwUgaGitA1pobVK+QfEXmR1uASovAiSqYiy3vN0aLiQI/oW'
           '5gfMgKBfb0jDv9eTh+V8az4akrxV7HejMWxM+odhlaXTvT30VIpuvjndCGXR7G'
           '9PCyALf050VstpepLuxj+eGV9T/pfZ+XrUAVlZneIoNFr41ucR7TwskrgeLRRF'
           '/fTYu9gw9rLYNhjzbJIOuAXLLcHXFQY4EXxRvy/pE5Fj4Z5yI8P/u0yNRgSCjW'
           'xO+hr1qwY62k6cW2TBDxU2G+i7UOQlPii2lUg42cy14bguPQVlZPat/yMfg1r8'
           'Co/MPXQ1MG3H2O4SdTjSTOsKviunZNOQ== testuser@gmail.com')


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
        project_id = self.cfg.project_id
        self.trace('Set common metadata options {}'.format(options))
        request = self.projects.setCommonInstanceMetadata(
            project=project_id,
            body=options)
        self._execute_async_request(request, project_id)

    @staticmethod
    def _get_expected_common_metadata(options):
        meta = copy.deepcopy(options)
        meta.setdefault('kind', 'compute#metadata')
        # TODO(alexey-mr): fingerprint is not supported
        # meta.setdefault('fingerprint', '.*')
        return meta

    def _get_expected_project(self, options):
        project = copy.deepcopy(options)
        name = project['name']
        project.setdefault('kind', 'compute#project')
        project.setdefault('selfLink', self.api.get_global_url(name))
        project.setdefault('id', '[0-9]+')
        # TODO(alexey-mr): creationTimestamp not supported
        # project.setdefault('creationTimestamp', '.*')
        project.setdefault('quotas', [])
        expected_common_metadata = self._get_expected_common_metadata(
            project.get('commonInstanceMetadata', dict()))
        project['commonInstanceMetadata'] = expected_common_metadata
        return project

    def test_get_project(self):
        project = self._get_project()
        options = {'name': self.cfg.project_id}
        expected_project = self._get_expected_project(options)
        self.assertObject(expected_project, project)

    def test_set_common_metadata(self):
        if not self.full_compatibility:
            # TODO(alexey-mr): OS GCE supports only sshKeys
            self.skipTest('OS GCE API does not support common metadata '
                          'except of sshKeys')
            return
        # save current project metadata
        before_test_state = self._get_project()
        before_test_metadata = before_test_state['commonInstanceMetadata']
        if 'fingerprint' in before_test_metadata:
            fingerprint = {
                'fingerprint': before_test_metadata.get('fingerprint')
            }
            before_test_metadata.pop('fingerprint', None)
        else:
            fingerprint = dict()
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
        before_test_state['commonInstanceMetadata'].update(fingerprint)
        self.assertObject(before_test_state, project)

    def test_set_common_metadata_ssh_keys(self):
        # save current project metadata
        before_test_state = self._get_project()
        before_test_metadata = before_test_state['commonInstanceMetadata']
        before_test_metadata.pop('kind', None)
        before_test_metadata.pop('fingerprint', None)
        self._add_cleanup(self._set_common_metadata, before_test_metadata)
        # do test
        metadata = {
            'items': [
                {
                    'key': 'sshKeys',
                    'value': SSH_KEY
                }
            ]
        }
        self._set_common_metadata(metadata)
        project = self._get_project()
        # make 're template' from ssh key because assertObject use re.match
        metadata['items'][0]['value'] = test_base.string_to_re_pattern(SSH_KEY)
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
        # make 're template' from ssh key because assertObject use re.match
        for i in before_test_metadata.get('items', []):
            if i['key'] == 'sshKeys':
                i['value'] = test_base.string_to_re_pattern(i['value'])
        # check object
        self.assertObject(before_test_state, project)
