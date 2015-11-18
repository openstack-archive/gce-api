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

from gceapi.tests.unit.api import common

FAKE_LOCAL_ROUTE_1 = {
    u'priority': 1000,
    u'kind': u'compute#route',
    u'description': u'Default route to the virtual network.',
    u'name': u'default-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-local',
    u'nextHopNetwork': (u'http://localhost/compute/v1beta15/projects/'
                        'fake_project/global/networks/private'),
    u'destRange': u'10.0.0.0/24',
    u'id': u'6109690470355354668',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/global/routes/'
                  'default-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-local'),
    u'network': (u'http://localhost/compute/v1beta15/projects/'
                 'fake_project/global/networks/private'),
    u'creationTimestamp': u'',
}
FAKE_INTERNET_ROUTE_1 = {
    u'nextHopGateway': (
        u'http://localhost/compute/v1beta15/projects/'
        'fake_project/global/gateways/default-internet-gateway'),
    u'kind': u'compute#route',
    u'description': u'Default route to the Internet.',
    u'name': u'default-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-internet',
    u'priority': 1000,
    u'destRange': u'0.0.0.0/0',
    u'id': u'6686112297298011631',
    u'selfLink': (
        u'http://localhost/compute/v1beta15/projects/'
        'fake_project/global/routes/'
        'default-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-internet'),
    u'network': (u'http://localhost/compute/v1beta15/projects/'
                 'fake_project/global/networks/private'),
    u'creationTimestamp': u'',
}
FAKE_CUSTOM_ROUTE_1 = {
    u'kind': u'compute#route',
    u'name': u'custom-route-1',
    u'description': u'route for 32.44.64.0/24',
    u'priority': 1000,
    u'nextHopIp': u'10.0.0.32',
    u'destRange': u'32.44.64.0/24',
    u'id': u'8814469654458772789',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/global/routes/custom-route-1'),
    u'network': (u'http://localhost/compute/v1beta15/projects/'
                 'fake_project/global/networks/private'),
    u'creationTimestamp': u'2013-12-25T09:05:07.396957Z',
}
FAKE_CUSTOM_ROUTE_2 = {
    u'kind': u'compute#route',
    u'name': (u'custom-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-'
              'dst-89-34-0-0-16-gw-10-0-0-78'),
    u'priority': 1000,
    u'nextHopIp': u'10.0.0.78',
    u'destRange': u'89.34.0.0/16',
    u'id': u'4048181833789971692',
    u'selfLink': (
        u'http://localhost/compute/v1beta15/projects/'
        'fake_project/global/routes/custom-route-'
        '734b9c83-3a8b-4350-8fbf-d40f571ee163-dst-89-34-0-0-16-gw-10-0-0-78'),
    u'network': (u'http://localhost/compute/v1beta15/projects/'
                 'fake_project/global/networks/private'),
    u'creationTimestamp': u'',
}
FAKE_LOCAL_ROUTE_2 = {
    u'priority': 1000,
    u'kind': u'compute#route',
    u'description': u'Default route to the virtual network.',
    u'name': u'default-route-7aa33661-33ba-4291-a2c7-44bfd59884c1-local',
    u'nextHopNetwork': (u'http://localhost/compute/v1beta15/projects/'
                        'fake_project/global/networks/public'),
    u'destRange': u'172.24.4.224/28',
    u'id': u'2822661357924528032',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/global/routes/'
                  'default-route-7aa33661-33ba-4291-a2c7-44bfd59884c1-local'),
    u'network': (u'http://localhost/compute/v1beta15/projects/'
                 'fake_project/global/networks/public'),
    u'creationTimestamp': u'',
}


class RoutesControllerTest(common.GCEControllerTest):
    """
    Test of the GCE API /routes application controller w/Neutron.
    """

    def test_list_routes(self):
        response = self.request_gce('/fake_project/global/routes')
        self.assertEqual(200, response.status_int)
        response_body = response.json_body
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#routeList",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/global/routes",
            "id": "projects/fake_project/global/routes",
        }
        response_routes = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertItemsEqual(
                [FAKE_LOCAL_ROUTE_1, FAKE_INTERNET_ROUTE_1,
                 FAKE_CUSTOM_ROUTE_1, FAKE_CUSTOM_ROUTE_2, FAKE_LOCAL_ROUTE_2],
                response_routes)

    def test_get_route(self):
        response = self.request_gce('/fake_project/global/routes/'
                                    'custom-route-1')
        self.assertEqual(200, response.status_int)
        response_body = response.json_body
        self.assertDictEqual(FAKE_CUSTOM_ROUTE_1, response_body)

    def test_get_local_route(self):
        response = self.request_gce(
                '/fake_project/global/routes/'
                'default-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-local')
        self.assertEqual(200, response.status_int)
        response_body = response.json_body
        self.assertDictEqual(FAKE_LOCAL_ROUTE_1, response_body)

    def test_get_nonexistent_route(self):
        response = self.request_gce(
                '/fake_project/global/routes/'
                'nonexistent_route')
        self.assertEqual(404, response.status_int)

    def test_add_internet_route(self):
        request_body = {
            'destRange': '0.0.0.0/0',
            'name': 'custom-internet-route',
            'network': 'private',
            'nextHopGateway': (
                   'http://localhost/compute/v1beta15/projects/'
                   'fake_project/global/gateways/default-internet-gateway'),
            'priority': 1000,
        }
        response = self.request_gce('/fake_project/global/routes',
                                    method="POST",
                                    body=request_body)
        expected = {
            "operationType": "insert",
            "targetId": "3171351404482340798",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/routes/custom-internet-route",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_add_custom_route(self):
        request_body = {
            'destRange': '40.81.234.0/24',
            'name': 'custom-route',
            'network': 'private',
            'nextHopIp': '10.0.0.107',
            'priority': 1000,
        }
        response = self.request_gce('/fake_project/global/routes',
                                    method="POST",
                                    body=request_body)
        expected = {
            "operationType": "insert",
            "targetId": "7622192026776022193",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/routes/custom-route",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_add_duplicate_route(self):
        request_body = {
            'destRange': '40.81.234.0/24',
            'name': 'custom-route-1',
            'network': 'private',
            'nextHopIp': '10.0.0.107',
            'priority': 1000,
        }
        response = self.request_gce('/fake_project/global/routes',
                                    method="POST",
                                    body=request_body)
        self.assertEqual(400, response.status_int)

    def test_add_unsupported_route(self):
        request_body = {
            'destRange': '40.81.234.0/24',
            'name': 'instance-route',
            'network': 'private',
            'nextHopInstance': 'instance',
            'priority': 1000,
        }
        response = self.request_gce('/fake_project/global/routes',
                                    method="POST",
                                    body=request_body)
        self.assertEqual(400, response.status_int)

    def test_delete_local_route(self):
        response = self.request_gce(
                '/fake_project/global/routes/'
                'default-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-local',
                method="DELETE")
        self.assertEqual(400, response.status_int)

    def test_delete_internet_route(self):
        response = self.request_gce(
                '/fake_project/global/routes/'
                'default-route-734b9c83-3a8b-4350-8fbf-d40f571ee163-internet',
                method="DELETE")
        expected = {
            "operationType": "delete",
            "targetId": "6686112297298011631",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/routes/default-route-"
                          "734b9c83-3a8b-4350-8fbf-d40f571ee163-internet",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_delete_custom_route(self):
        response = self.request_gce(
                '/fake_project/global/routes/custom-route-1',
                method="DELETE")
        expected = {
            "operationType": "delete",
            "targetId": "8814469654458772789",
            "targetLink": "http://localhost/compute/v1beta15/projects/"
                          "fake_project/global/routes/custom-route-1",
        }
        expected.update(common.COMMON_FINISHED_OPERATION)
        self.assertEqual(200, response.status_int)
        self.assertDictEqual(expected, response.json_body)

    def test_delete_unexistent_route(self):
        response = self.request_gce(
                '/fake_project/global/routes/'
                'nonexistent-route',
                method="DELETE")
        self.assertEqual(404, response.status_int)
