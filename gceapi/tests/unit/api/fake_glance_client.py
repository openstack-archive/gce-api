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

import copy

from glanceclient import exc as glance_exc
from oslo_utils import timeutils

from gceapi.tests.unit.api import fake_request
from gceapi.tests.unit.api import utils


_TIMESTAMP = timeutils.parse_isotime('2013-08-01T11:30:25')
FAKE_IMAGES = [utils.FakeObject({
    'id': '60ff30c2-64b6-4a97-9c17-322eebc8bd60',
    'name': 'fake-image-1',
    'created_at': _TIMESTAMP,
    'updated_at': _TIMESTAMP,
    'deleted_at': None,
    'deleted': False,
    'status': 'active',
    'is_public': False,
    'container_format': 'bare',
    'disk_format': 'raw',
    'properties': {},
    'owner': fake_request.PROJECT_ID,
    'protected': False,
    'min_ram': 0,
    'checksum': u'50bdc35edb03a38d91b1b071afb20a3c',
    'min_disk': 0,
    'size': 1
}), utils.FakeObject({
    'id': 'a2459075-d96c-40d5-893e-577ff92e721c',
    'name': 'fake-image-2',
    'created_at': _TIMESTAMP,
    'updated_at': _TIMESTAMP,
    'deleted_at': None,
    'deleted': False,
    'status': 'active',
    'is_public': True,
    'container_format': 'bare',
    'disk_format': 'raw',
    'properties': {},
    'owner': fake_request.PROJECT_ID,
    'protected': False,
    'min_ram': 0,
    'checksum': u'20bdc35edb03a38d91b1b071afb20a3c',
    'min_disk': 0,
    'size': 2,
 }), utils.FakeObject({
    'id': '0aa076e2-def4-43d1-ae81-c77a9f9279e6',
    'name': 'image-to-delete',
    'created_at': _TIMESTAMP,
    'updated_at': _TIMESTAMP,
    'deleted_at': None,
    'deleted': False,
    'status': 'active',
    'is_public': True,
    'container_format': 'bare',
    'disk_format': 'raw',
    'properties': {},
    'owner': fake_request.PROJECT_ID,
    'protected': False,
    'min_ram': 0,
    'checksum': u'20bdc35edb03a38d91b1b071afb20a3c',
    'min_disk': 0,
    'size': 2,
})]

FAKE_NEW_IMAGE = {
    "new-image": {
        "id": "6a8fd89a-e636-48a4-8095-5510eab696c4",
        "created_at": timeutils.parse_isotime("2013-08-02T11:30:25"),
        "size": 5,
    }
}


class FakeImages(object):
    def get(self, image):
        image_id = utils.get_id(image)
        for i in FAKE_IMAGES:
            if i.id == image_id:
                return i

        raise glance_exc.HTTPNotFound()

    def list(self, **kwargs):
        filters = kwargs.get('filters', {})
        if "name" in filters:
            return [i for i in FAKE_IMAGES
                    if i.name == filters["name"]]

        return FAKE_IMAGES

    def delete(self, image):
        image_id = utils.get_id(image)
        image_index = 0
        for image in FAKE_IMAGES:
            if image.id != image_id:
                image_index += 1
                continue
            del FAKE_IMAGES[image_index]
            return True
        raise glance_exc.HTTPNotFound()

    def create(self, **kwargs):
        image = copy.deepcopy(FAKE_NEW_IMAGE[kwargs["name"]])
        image.update(kwargs)
        image["updated_at"] = image["created_at"]
        image.update({
            "deleted_at": False,
            "deleted": False,
            "status": "active",
        })
        FAKE_IMAGES.append(utils.FakeObject(image))
        return copy.deepcopy(utils.FakeObject(image))


class FakeGlanceClient(object):
    def __init__(self, version, *args, **kwargs):
        pass

    @property
    def images(self):
        return FakeImages()
