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

from gceapi.tests.functional.api import test_disks


class TestImages(test_disks.TestDiskBase):
    def _list_images(self, filter=None, project=None):
        project_id = project if project else self.cfg.project_id
        self.trace('List images: project_id={}'.format(project_id))
        request = self.images.list(project=project_id, filter=filter)
        result = request.execute()
        self.trace('Images: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='ImageList')
        return result

    def _prepare_disk(self):
        name = self._rand_name('testdisk')
        options = {
            'name': name
        }
        self._create_disk(options)
        return self._ensure_disk_created(options)

    def test_get_default_image(self):
        relative_image_url = self.cfg.image
        name, project = self._parse_image_url(relative_image_url)
        default_options = {
            'name': name,
            'selfLink': self.api.get_global_url(relative_image_url)
        }
        expected_image = self._get_expected_image(default_options)
        image = self._get_image(name, project)
        self.assertObject(expected_image, image)

    def test_list_default_images(self):
        relative_image_url = self.cfg.image
        name, project = self._parse_image_url(relative_image_url)
        default_options = {
            'name': name,
            'selfLink': self.api.get_global_url(relative_image_url)
        }
        expected_image = self._get_expected_image(default_options)
        result = self._list_images(project=project)
        image = self.assertFind(name, result)
        self.assertObject(expected_image, image)

    def test_list_default_images_by_filter_name(self):
        relative_image_url = self.cfg.image
        name, project = self._parse_image_url(relative_image_url)
        default_options = {
            'name': name,
            'selfLink': self.api.get_global_url(relative_image_url)
        }
        result = self._list_images(
            project=project,
            filter='name eq unexisting_image')
        self.assertNotFind(name, result)
        result = self._list_images(
            project=project,
            filter='name eq {}'.format(name))
        image = self.assertFind(name, result)
        expected_image = self._get_expected_image(default_options)
        self.assertObject(expected_image, image)

    def test_create_delete_image_from_disk(self):
        # TODO(alexey-mr): OS GCE does not support image creation from disk'
        if not self.full_compatibility:
            self.skipTest('OS GCE does not support image creation from disk')
            return
        # prepare disk for further image creation
        disk = self._prepare_disk()
        disk_name = disk['name']
        # do image creation
        name = self._rand_name('testimage')
        source_disk = 'zones/{}/disks/{}'.format(self.cfg.zone, disk_name)
        options = {
            'name': name,
            'sourceDisk': source_disk
        }
        self._create_image(options)
        # verify created image
        options['sourceDisk'] = disk['selfLink']  # full expected source url
        options['sourceDiskId'] = disk['id']  # add expected source id
        # TODO(alexey-mr): image diskSizeGb is not supported by OS GCE
        # options['diskSizeGb'] = disk['sizeGb']  # add expected size to check
        self._ensure_image_created(options)
        # delete resource
        self._delete_image(name)
        self._delete_disk(disk_name)

    def test_list_images(self):
        # TODO(alexey-mr): OS GCE does not support image creation from disk'
        if not self.full_compatibility:
            self.skipTest('OS GCE does not support image creation from disk')
            return
        # prepare resources
        disk = self._prepare_disk()
        image = self._create_image_from_disk(disk)
        image_name = image['name']
        # list and find object from server and check properties
        result = self._list_images()
        result = self.assertFind(image_name, result)
        self.assertObject(image, result)
        # remove resources
        self._delete_image(image_name)
        self._delete_disk(disk['name'])

    def test_list_images_by_filter_name(self):
        # TODO(alexey-mr): OS GCE does not support image creation from disk'
        if not self.full_compatibility:
            self.skipTest('OS GCE does not support image creation from disk')
            return
        # prepare resources
        disk = self._prepare_disk()
        images = list()
        for i in range(0, 3):
            images.append(self._create_image_from_disk(disk))
        # list images with filter by name
        for image in images:
            filter = 'name eq {}'.format(image['name'])
            result = self._list_images(filter=filter)
            self.assertEqual(1, len(result['items']))
            self.assertObject(image, result['items'][0])
        # clean resources
        for image in images:
            self._delete_image(image['name'])
        self._delete_disk(disk['name'])
