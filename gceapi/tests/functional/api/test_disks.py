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


class TestSnapshotsBase(test_base.GCETestCase):
    @property
    def snapshots(self):
        res = self.api.compute.snapshots()
        self.assertIsNotNone(
            res,
            'Null snapshots object, api is not built properly')
        return res

    def _delete_snapshot(self, name):
        project_id = self.cfg.project_id
        self.trace('Delete snapshot: project_id={} name={}'.
                   format(project_id, name))
        request = self.snapshots.delete(
            project=project_id,
            snapshot=name)
        self._execute_async_request(request, project_id)
        self._remove_cleanup(self._delete_snapshot, name)

    def _list_snapshots(self, filter=None):
        project_id = self.cfg.project_id
        self.trace('List snapshots: project_id={}'.format(project_id))
        request = self.snapshots.list(project=project_id, filter=filter)
        result = request.execute()
        self.trace('Snapshots: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='SnapshotList')
        return result

    def _get_snapshot(self, name):
        project_id = self.cfg.project_id
        self.trace('Get snapshot: project_id={} name={}'.
                   format(project_id, name))
        request = self.snapshots.get(
            project=project_id,
            snapshot=name)
        result = request.execute()
        self.trace('Snapshot: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Snapshot')
        return result

    def _get_expected_snapshot(self, disk_name, options):
        snapshot = copy.deepcopy(options)
        # fill defaults if needed
        snapshot.setdefault('kind', 'compute#snapshot')
        if 'selfLink' not in options:
            snapshot_url = 'global/snapshots/{}'.format(snapshot['name'])
            snapshot['selfLink'] = self.api.get_project_url(snapshot_url)
        snapshot.setdefault('status', 'READY')
        if 'sourceDisk' not in options:
            src_disk_url = 'disks/{}'.format(disk_name)
            snapshot['sourceDisk'] = self.api.get_zone_url(src_disk_url)
        return snapshot

    def _ensure_snapshot_created(self, disk_name, options):
        name = options['name']
        snapshot = self._get_expected_snapshot(disk_name, options)
        # get object from server and check properties
        result = self._get_snapshot(name)
        self.assertObject(snapshot, result)
        return result


class TestImagesBase(TestSnapshotsBase):
    @property
    def images(self):
        res = self.api.compute.images()
        self.assertIsNotNone(
            res,
            'Null images object, api is not built properly')
        return res

    def _create_image(self, options):
        name = options['name']
        cfg = self.cfg
        project_id = cfg.project_id
        self.trace('Create image {}'.format(options))
        request = self.images.insert(
            project=project_id,
            body=options)
        self._add_cleanup(self._delete_image, name)
        self._execute_async_request(request, project_id)

    def _delete_image(self, name):
        project_id = self.cfg.project_id
        self.trace('Delete image: project_id={} name={}'.
                   format(project_id, name))
        request = self.images.delete(
            project=project_id,
            image=name)
        self._execute_async_request(request, project_id)
        self._remove_cleanup(self._delete_image, name)

    def _get_image(self, name, project=None):
        project_id = project if project else self.cfg.project_id
        self.trace('Get image: project_id={} name={}'.
                   format(project_id, name))
        request = self.images.get(
            project=project_id,
            image=name)
        result = request.execute()
        self.trace('Image: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Image')
        return result

    @staticmethod
    def _parse_image_url(image_url):
        parsed_url = image_url.split('/')
        name = parsed_url[-1]
        project = parsed_url[-4]
        return name, project

    def _get_image_size(self, image_url):
        name, project = self._parse_image_url(image_url)
        image = self._get_image(name, project)
        return image['diskSizeGb']

    def _get_expected_image(self, options):
        image = copy.deepcopy(options)
        image.setdefault('kind', 'compute#image')
        if 'selfLink' not in image:
            relative_url = 'global/images/{}'.format(image['name'])
            image['selfLink'] = self.api.get_project_url(relative_url)
        image.setdefault('sourceType', 'RAW')
        image.setdefault('status', 'READY')
        return image

    def _ensure_image_created(self, options):
        name = options['name']
        image = self._get_expected_image(options)
        # get object from server and check properties
        result = self._get_image(name)
        self.assertObject(image, result)
        return result

    def _create_image_from_disk(self, disk):
        name = self._rand_name('testimage')
        options = {
            'name': name,
            'sourceDisk': disk['selfLink']
        }
        self._create_image(options)
        options['sourceDisk'] = disk['selfLink']
        options['sourceDiskId'] = disk['id']
        # TODO(alexey-mr): image diskSizeGb is not supported by OS GCE
        # options['diskSizeGb'] = disk['sizeGb']
        return self._ensure_image_created(options)


class TestDiskBase(TestImagesBase):
    @property
    def disks(self):
        res = self.api.compute.disks()
        self.assertIsNotNone(
            res,
            'Null disks object, api is not built properly')
        return res

    def _create_disk(self, options, source_image=None):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('Create disk with options {} source_image={}'.
                   format(options, source_image))
        request = self.disks.insert(
            project=project_id,
            zone=zone,
            sourceImage=source_image,
            body=options)
        self._add_cleanup(self._delete_disk, options['name'])
        self._execute_async_request(request, project_id, zone=zone)

    def _delete_disk(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('Delete disk: project_id={} zone={} name={}'.
                   format(project_id, zone, name))
        request = self.disks.delete(
            project=project_id,
            zone=zone,
            disk=name)
        self._execute_async_request(request, project_id, zone=zone)
        self._remove_cleanup(self._delete_disk, name)

    def _list_disks(self, filter=None):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('List disks: project_id={} zone={} filter={}'.
                   format(project_id, zone, filter))
        request = self.disks.list(
            project=project_id,
            zone=zone,
            filter=filter)
        result = request.execute()
        self.trace('Disks: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='DiskList')
        return result

    def _get_disk(self, name):
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('Get disk: project_id={} zone={} name={}'.
                   format(project_id, zone, name))
        request = self.disks.get(
            project=project_id,
            zone=zone,
            disk=name)
        result = request.execute()
        self.trace('Disk: {}'.format(result))
        self.api.validate_schema(value=result, schema_name='Disk')
        return result

    def _get_expected_disk(self, options, source_image=None):
        disk = copy.deepcopy(options)
        # fill defaults if needed
        disk.setdefault('kind', 'compute#disk')
        disk.setdefault('sizeGb', '500' if self.full_compatibility else '1')
        disk.setdefault('zone', self.api.get_zone_url())
        if 'selfLink' not in disk:
            disk_url = 'disks/{}'.format(options['name'])
            disk['selfLink'] = self.api.get_zone_url(disk_url)
        # TODO(alexey-mr): disk-types are note supported by OS GCE
        # if 'type' not in disk:
        #     disk['type'] = self.api.get_zone_url('diskTypes/pd-standard')
        disk.setdefault('status', 'READY')
        if 'sourceSnapshot' in options:
            snapshot_url = self.api.get_project_url(options['sourceSnapshot'])
            disk['sourceSnapshot'] = snapshot_url
        if source_image is not None:
            disk['sourceImage'] = self.api.get_global_url(source_image)
        return disk

    def _ensure_disk_created(self, options, source_image=None):
        name = options['name']
        disk = self._get_expected_disk(options, source_image)
        # get object from server and check properties
        result = self._get_disk(name)
        self.assertObject(disk, result)
        return result

    def _create_disk_from_image(self, image):
        name = self._rand_name('testdisk')
        options = {
            'name': name,
        }
        self._create_disk(options, source_image=image['selfLink'])
        options['sourceImage'] = image['selfLink']
        options['sourceImageId'] = image['id']
        if self.full_compatibility:
            # TODO(alexey-mr): image diskSizeGb is not supported by OS GCE
            options['sizeGb'] = image['diskSizeGb']
        return self._ensure_disk_created(options)

    def _create_snapshot(self, disk_name, options):
        name = options['name']
        cfg = self.cfg
        project_id = cfg.project_id
        zone = cfg.zone
        self.trace('Create snapshot {} for disk={}'.format(name, disk_name))
        request = self.disks.createSnapshot(
            project=project_id,
            zone=zone,
            disk=disk_name,
            body=options)
        self._add_cleanup(self._delete_snapshot, name)
        self._execute_async_request(request, project_id, zone=zone)

    def _create_disk_and_snapshot(self):
        # prepare disk for snapshot
        disk_name = self._rand_name('testdisk')
        disk_options = {
            'name': disk_name,
            'sizeGb': '1'
        }
        self._create_disk(disk_options)
        disk = self._ensure_disk_created(disk_options)
        # prepare snapshot
        snapshot_name = self._rand_name('testsnapshot')
        snapshot_options = {
            'name': snapshot_name
        }
        self._create_snapshot(disk_name=disk_name, options=snapshot_options)
        snapshot_options['diskSizeGb'] = disk_options['sizeGb']
        snapshot = self._ensure_snapshot_created(disk_name=disk_name,
                                                 options=snapshot_options)
        return {'disk': disk, 'snapshot': snapshot}


class TestDisks(TestDiskBase):
    def test_create_delete_default_disk(self):
        name = self._rand_name('testdisk')
        options = {
            'name': name
        }
        self._create_disk(options)
        self._ensure_disk_created(options)
        self._delete_disk(name)

    def test_create_delete_disk_with_size(self):
        name = self._rand_name('testdisk')
        options = {
            'name': name,
            'sizeGb': None
        }
        for size in ['1', '2']:
            options['sizeGb'] = size
            self._create_disk(options)
            self._ensure_disk_created(options)
            self._delete_disk(name)

    def test_create_disk_from_image(self):
        image_name, image_project = self._parse_image_url(self.cfg.image)
        image = self._get_image(image_name, image_project)
        disk = self._create_disk_from_image(image)
        # TODO(alexey-mr): image diskSizeGb is not supported by OS GCE
        # options['sizeGb'] = self._get_image_size(self.cfg.image)
        self._delete_disk(disk['name'])

    def test_create_disk_from_snapshot(self):
        data = self._create_disk_and_snapshot()
        snapshot = data['snapshot']
        snapshot_name = snapshot['name']
        # create testing disk by snapshot
        disk_name = self._rand_name('testdisk')
        snapshot_url = 'global/snapshots/{}'.format(snapshot_name)
        options = {
            'name': disk_name,
            'sourceSnapshot': snapshot_url
        }
        self._create_disk(options)
        options['sizeGb'] = snapshot['diskSizeGb']
        self._ensure_disk_created(options)
        # delete resources
        self._delete_disk(disk_name)
        self._delete_snapshot(snapshot_name)
        self._delete_disk(data['disk']['name'])

    def test_list_disks(self):
        # create disks
        name = self._rand_name('testdisk')
        options = {
            'name': name,
            'sizeGb': '1'
        }
        self._create_disk(options)
        disk = self._ensure_disk_created(options)
        # list and find object from server and check properties
        result = self._list_disks()
        result = self.assertFind(name, result)
        self.assertObject(disk, result)
        self._delete_disk(name)

    def test_list_disks_by_filter_name(self):
        # prepare disks
        names = list()
        for i in range(0, 3):
            names.append(self._rand_name('testdisk'))
        disks = dict()
        for name in names:
            options = {
                'name': name,
                'sizeGb': '1'
            }
            self._create_disk(options)
            disks[name] = self._ensure_disk_created(options)
        # list disks with filter by name
        for name in names:
            result = self._list_disks(filter='name eq {}'.format(name))
            self.assertEqual(1, len(result['items']))
            self.assertObject(disks[name], result['items'][0])
        # clean resources
        for name in names:
            self._delete_disk(name)
