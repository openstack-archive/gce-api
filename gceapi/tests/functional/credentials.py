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


from keystoneclient.client import Client as KeystoneClient
from oauth2client.client import AccessTokenCredentials
from oauth2client.client import GoogleCredentials


class CredentialsProvider(object):
    def __init__(self, supp):
        self._supp = supp

    def _trace(self, msg):
        self._supp.trace(msg)

    def _get_app_credentials(self):
        self._trace('Create GoogleCredentials from default app file')
        return GoogleCredentials.get_application_default()

    def _get_token_crenetials(self):
        cfg = self._supp.cfg
        auth_data = {
            'username': cfg.username,
            'password': cfg.password,
            'tenant_name': cfg.project_id,
            'auth_url': cfg.auth_url
        }
        self._trace('Auth data {}'.format(auth_data))
        client = KeystoneClient(**auth_data)
        if not client.authenticate():
            raise Exception('Failed to authenticate user')
        token = client.auth_token
        self._trace('Created token {}'.format(token))
        return AccessTokenCredentials(access_token=token,
                                      user_agent='GCE test')

    @property
    def credentials(self):
        cred_type = self._supp.cfg.cred_type
        if cred_type == 'os_token':
            return self._get_token_crenetials()
        elif cred_type == 'gcloud_auth':
            return self._get_app_credentials()
        else:
            raise Exception('Unknown cred_type {}'.format(cred_type))
