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

from gceapi import context
from gceapi import wsgi_ext as os_wsgi


PROJECT_ID = "4a5cc7d8893544a9babb3b890227d75e"
REGION = u'region-one'

FAKE_SERVICE_CATALOG = [{
    u'endpoints': [{
        u'adminURL': u'http://192.168.137.21:8774/v2/' + PROJECT_ID,
        u'region': REGION,
        u'id': u'81a8b36abc5f4945bbd1269be0423012',
        u'internalURL': u'http://192.168.137.21:8774/v2/' + PROJECT_ID,
        u'publicURL': u'http://192.168.137.21:8774/v2/' + PROJECT_ID}],
    u'endpoints_links': [],
    u'type': u'compute',
    u'name': u'nova'
}, {
    u'endpoints': [{
        u'adminURL': u'http://192.168.137.21:9696/',
        u'region': REGION,
        u'id': u'10a0fc598a5741c390f0d6560a89fced',
        u'internalURL': u'http://192.168.137.21:9696/',
        u'publicURL': u'http://192.168.137.21:9696/'}],
    u'endpoints_links': [],
    u'type': u'network',
    u'name': u'neutron'
}, {
    u'endpoints': [{
        u'adminURL': u'http://192.168.137.21:9292',
        u'region': REGION,
        u'id': u'39643060448c4c089535fce07f2d2aa4',
        u'internalURL': u'http://192.168.137.21:9292',
        u'publicURL': u'http://192.168.137.21:9292'}],
    u'endpoints_links': [],
    u'type': u'image',
    u'name': u'glance'
}, {
    u'endpoints': [{
        u'adminURL': u'http://192.168.137.21:8776/v1/' + PROJECT_ID,
        u'region': REGION,
        u'id': u'494bd5333aed467092316e03b1163139',
        u'internalURL': u'http://192.168.137.21:8776/v1/' + PROJECT_ID,
        u'publicURL': u'http://192.168.137.21:8776/v1/' + PROJECT_ID}],
    u'endpoints_links': [],
    u'type': u'volume',
    u'name': u'cinder'
}]


class HTTPRequest(os_wsgi.Request):

    @classmethod
    def blank(cls, url, has_body=False, *args, **kwargs):
        kwargs['base_url'] = 'http://localhost/compute/v1beta15/projects'
        if has_body:
            kwargs.setdefault("content_type", "application/json")
        out = os_wsgi.Request.blank(url, *args, **kwargs)
        user_id = 'c2bc8099-8861-46ab-a416-99f06bb89198'
        user_name = 'fake_user'
        project_id = PROJECT_ID
        project_name = 'fake_project'
        fake_context = context.RequestContext(user_id,
                                              project_id,
                                              user_name=user_name,
                                              project_name=project_name,
                                              is_admin=True)
        fake_context.service_catalog = FAKE_SERVICE_CATALOG
        out.environ['gceapi.context'] = fake_context
        return out
