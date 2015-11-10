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


from keystoneclient import client as keystone_client
from oauth2client import client as oauth_client


class CredentialsProvider(object):
    def __init__(self, cfg):
        self.cfg = cfg

    @staticmethod
    def _get_app_credentials():
        return oauth_client.GoogleCredentials.get_application_default()

    def _get_token_credentials(self):
        client = self._create_keystone_client()
        token = client.auth_token
        return oauth_client.AccessTokenCredentials(
            access_token=token,
            user_agent='GCE test')

    def _create_keystone_client(self):
        cfg = self.cfg
        auth_data = {
            'username': cfg.username,
            'password': cfg.password,
            'tenant_name': cfg.project_id,
            'auth_url': cfg.auth_url
        }
        client = keystone_client.Client(**auth_data)
        if not client.authenticate():
            raise Exception('Failed to authenticate user')
        return client

    @property
    def keystone_client(self):
        return self._create_keystone_client()

    @property
    def is_google_auth(self):
        return self.cfg.cred_type == 'gcloud_auth'

    @property
    def credentials(self):
        cred_type = self.cfg.cred_type
        if cred_type == 'os_token':
            return self._get_token_credentials()
        elif cred_type == 'gcloud_auth':
            return self._get_app_credentials()
        else:
            raise Exception('Unknown cred_type {}'.format(cred_type))
