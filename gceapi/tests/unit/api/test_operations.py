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

from gceapi.api import operations
from gceapi.tests.unit.api import common

FAKE_ADD_INSTANCE = {
    u'status': u'RUNNING',
    u'kind': u'compute#operation',
    u'operationType': u'add',
    u'zone': (u'http://localhost/compute/v1beta15/projects/'
              'fake_project/zones/nova'),
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'3991024138321713624',
    u'name': u'operation-47be73d8-b8fe-4148-9e3b-3f323136ee57',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/zones/nova/instances/i1'),
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'progress': 0,
    u'id': u'2720525776854968247',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/zones/nova/operations/'
                  'operation-47be73d8-b8fe-4148-9e3b-3f323136ee57'),
    u'user': u'admin'
}
FAKE_DELETE_INSTANCE = {
    u'status': u'RUNNING',
    u'kind': u'compute#operation',
    u'operationType': u'delete',
    u'zone': (u'http://localhost/compute/v1beta15/projects/'
              'fake_project/zones/nova'),
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'6879239049877988420',
    u'name': u'operation-fbd91157-91e9-4121-af74-090260aa38cc',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/zones/nova/instances/i-deleted'),
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'progress': 0,
    u'id': u'5384375190177147022',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/zones/nova/operations/'
                  'operation-fbd91157-91e9-4121-af74-090260aa38cc'),
    u'user': u'admin'
}
FAKE_RESET_INSTANCE = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'operationType': u'reset',
    u'zone': (u'http://localhost/compute/v1beta15/projects/'
              'fake_project/zones/nova'),
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'3991024138321713621',
    u'name': u'operation-6fc4e7e2-c0c8-4f97-bf1d-f6f958eb17b7',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/zones/nova/instances/i2'),
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'progress': 100,
    u'endTime': u'2013-12-27T08:46:34.684354Z',
    u'id': u'1756014432056394800',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/zones/nova/operations/'
                  'operation-6fc4e7e2-c0c8-4f97-bf1d-f6f958eb17b7'),
    u'user': u'admin'
}
FAKE_ADD_DISK = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'operationType': u'add',
    u'zone': (u'http://localhost/compute/v1beta15/projects/'
              'fake_project/zones/nova'),
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'9202387718698825408',
    u'name': u'operation-05e2a2b2-9708-4386-97cc-2318df3357b6',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/zones/nova/disks/fake-disk-1'),
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'progress': 100,
    u'endTime': u'2013-12-27T08:46:34.684354Z',
    u'id': u'5828976712396009927',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/zones/nova/operations/'
                  'operation-05e2a2b2-9708-4386-97cc-2318df3357b6'),
    u'user': u'admin'
}
FAKE_DELETE_DISK = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'operationType': u'delete',
    u'zone': (u'http://localhost/compute/v1beta15/projects/'
              'fake_project/zones/nova'),
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'3806967300998164012',
    u'name': u'operation-1cfd73fa-9b79-43ef-bbc7-c44bc514ba2e',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/zones/nova/disks/fake-deleted-disk'),
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'progress': 100,
    u'endTime': u'2013-12-27T08:46:34.684354Z',
    u'id': u'1352585941258466199',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/zones/nova/operations/'
                  'operation-1cfd73fa-9b79-43ef-bbc7-c44bc514ba2e'),
    u'user': u'admin'
}
FAKE_CREATE_SNAPSHOT = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'operationType': u'createSnapshot',
    u'zone': (u'http://localhost/compute/v1beta15/projects/'
              'fake_project/zones/nova'),
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'9202387718698825406',
    u'name': u'operation-3f6f1326-3e7c-4076-be6b-939147d031ae',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/zones/nova/disks/fake-disk-3'),
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'progress': 100,
    u'endTime': u'2013-12-27T08:46:34.684354Z',
    u'id': u'8142453451801876697',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/zones/nova/operations/'
                  'operation-3f6f1326-3e7c-4076-be6b-939147d031ae'),
    u'user': u'admin'
}
FAKE_DELETE_SNAPSHOT = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'4046627746386228297',
    u'name': u'operation-e72badca-0273-4a69-9303-181df05e602c',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/global/snapshots/fake-deleted-snapshot'),
    u'operationType': u'delete',
    u'progress': 100,
    u'endTime': u'2013-12-27T08:46:34.684354Z',
    u'id': u'3651183053589617825',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/global/operations/'
                  'operation-e72badca-0273-4a69-9303-181df05e602c'),
    u'user': u'admin'
}
FAKE_ADD_IMAGE = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'5721131091780319465',
    u'name': u'operation-9417e8bd-e8cc-47a1-86e8-c4c24c043b3d',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/global/images/fake-image-1'),
    u'operationType': u'add',
    u'progress': 100,
    u'endTime': u'2013-12-27T08:46:34.684354Z',
    u'id': u'939083621940800216',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/global/operations/'
                  'operation-9417e8bd-e8cc-47a1-86e8-c4c24c043b3d'),
    u'user': u'admin'
}
FAKE_DELETE_IMAGE = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'5396967400190520435',
    u'name': u'operation-0aad68c4-ee6b-45da-af7e-9e696a885168',
    u'targetLink': (u'http://localhost/compute/v1beta15/projects/'
                    'fake_project/global/images/fake-deleted-image'),
    u'operationType': u'delete',
    u'progress': 100,
    u'endTime': u'2013-12-27T08:46:34.684354Z',
    u'id': u'984725436897145210',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/global/operations/'
                  'operation-0aad68c4-ee6b-45da-af7e-9e696a885168'),
    u'user': u'admin'
}
FAKE_SET_METADATA = {
    u'status': u'DONE',
    u'kind': u'compute#operation',
    u'insertTime': u'2014-01-20T11:17:39.735738Z',
    u'startTime': u'2014-01-20T11:17:39.935278Z',
    u'targetId': u'504224095749693425',
    u'name': u'operation-a7b6bb82-d51f-4f04-a07c-bd9241bc2aac',
    u'targetLink': u'http://localhost/compute/v1beta15/projects/fake_project',
    u'operationType': u'setMetadata',
    u'progress': 100,
    u'endTime': u'2014-01-20T11:17:43.378890Z',
    u'id': u'6371605128170593585',
    u'selfLink': (u'http://localhost/compute/v1beta15/projects/'
                  'fake_project/global/operations/'
                  'operation-a7b6bb82-d51f-4f04-a07c-bd9241bc2aac'),
    u'user': u'admin'
}


class OperationsControllerTest(common.GCEControllerTest):

    def setUp(self):
        """Run before each test."""
        super(OperationsControllerTest, self).setUp()
        self.controller = operations.Controller()

    def test_aggregated_list_combined_with_update_progress(self):
        response = self.request_gce('/fake_project/aggregated/operations')
        self.assertEqual(200, response.status_int)
        response_body = response.json_body
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#operationAggregatedList",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/aggregated/operations",
            "id": "projects/fake_project/aggregated/operations",
        }
        operation_dict = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertIn("global", operation_dict)
        self.assertIn("operations", operation_dict["global"])
        operations = operation_dict["global"].pop("operations")
        self.assertItemsEqual([FAKE_DELETE_SNAPSHOT,
                               FAKE_ADD_IMAGE, FAKE_DELETE_IMAGE,
                               FAKE_SET_METADATA], operations)
        self.assertEqual(0, len(operation_dict["global"]))
        operation_dict.pop("global")
        self.assertIn("zones/nova", operation_dict)
        self.assertIn("operations", operation_dict["zones/nova"])
        operations = operation_dict["zones/nova"].pop("operations")
        self.assertItemsEqual([FAKE_ADD_INSTANCE, FAKE_DELETE_INSTANCE,
                               FAKE_RESET_INSTANCE,
                               FAKE_ADD_DISK, FAKE_DELETE_DISK,
                               FAKE_CREATE_SNAPSHOT], operations)
        self.assertEqual(0, len(operation_dict["zones/nova"]))
        operation_dict.pop("zones/nova")
        self.assertEqual(0, len(operation_dict))

    def test_list_zone_operations(self):
        response = self.request_gce('/fake_project/zones/nova/operations')
        self.assertEqual(200, response.status_int)
        response_body = response.json_body
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#operationList",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/zones/nova/operations",
            "id": "projects/fake_project/zones/nova/operations",
        }
        operations = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertItemsEqual([FAKE_ADD_INSTANCE, FAKE_DELETE_INSTANCE,
                               FAKE_RESET_INSTANCE,
                               FAKE_ADD_DISK, FAKE_DELETE_DISK,
                               FAKE_CREATE_SNAPSHOT], operations)

    def test_list_global_operations(self):
        response = self.request_gce('/fake_project/global/operations')
        self.assertEqual(200, response.status_int)
        response_body = response.json_body
        self.assertIn("items", response_body)
        expected_common = {
            "kind": "compute#operationList",
            "selfLink": "http://localhost/compute/v1beta15/projects/"
                        "fake_project/global/operations",
            "id": "projects/fake_project/global/operations",
        }
        operations = response_body.pop("items")
        self.assertDictEqual(expected_common, response_body)
        self.assertItemsEqual([FAKE_DELETE_SNAPSHOT,
                               FAKE_ADD_IMAGE, FAKE_DELETE_IMAGE,
                               FAKE_SET_METADATA], operations)

    def test_get_global_operation(self):
        response = self.request_gce(
                '/fake_project/global/operations/'
                'operation-a7b6bb82-d51f-4f04-a07c-bd9241bc2aac')
        self.assertEqual(200, response.status_int)
        self.assertEqual(FAKE_SET_METADATA, response.json_body)

    def test_get_zone_operation(self):
        response = self.request_gce(
                '/fake_project/zones/nova/operations/'
                'operation-05e2a2b2-9708-4386-97cc-2318df3357b6')
        self.assertEqual(200, response.status_int)
        self.assertEqual(FAKE_ADD_DISK, response.json_body)

    def test_get_global_operation_from_zone(self):
        response = self.request_gce(
                '/fake_project/zones/nova/operations/'
                'operation-a7b6bb82-d51f-4f04-a07c-bd9241bc2aac')
        self.assertEqual(404, response.status_int)

    def test_get_zone_operation_from_global(self):
        response = self.request_gce(
                '/fake_project/global/operations/'
                'operation-05e2a2b2-9708-4386-97cc-2318df3357b6')
        self.assertEqual(404, response.status_int)

    def test_delete_operation(self):
        response = self.request_gce(
                '/fake_project/global/operations/'
                'operation-a7b6bb82-d51f-4f04-a07c-bd9241bc2aac',
                method="DELETE")
        self.assertEqual(204, response.status_int)

    def test_delete_operation_from_other_scope(self):
        response = self.request_gce(
                '/fake_project/zones/nova/operations/'
                'operation-a7b6bb82-d51f-4f04-a07c-bd9241bc2aac',
                method="DELETE")
        self.assertEqual(204, response.status_int)
