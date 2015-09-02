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
import inspect
import uuid

from novaclient import client as novaclient

from gceapi.api import base_api
from gceapi.i18n import _
from gceapi.tests.unit.api import fake_request
from gceapi.tests.unit.api import utils


FAKE_DETAILED_ZONES = [utils.FakeObject({
    "zoneState": {
        "available": True},
    "hosts": {
        "grizzly": {
            "nova-conductor": {
                "available": True,
                "active": True,
                "updated_at": "2013-12-24T14:14:47.000000"},
            "nova-consoleauth": {
                "available": True,
                "active": True,
                "updated_at": "2013-12-24T14:14:49.000000"},
            "nova-scheduler": {
                "available": True,
                "active": True,
                "updated_at": "2013-12-24T14:14:48.000000"},
            "nova-cert": {
                "available": True,
                "active": True,
                "updated_at": "2013-12-24T14:14:49.000000"}}},
    "zoneName": "internal"
}), utils.FakeObject({
    "zoneState": {
        "available": True},
    "hosts": {
        "grizzly": {
            "nova-compute": {
                "available": True,
                "active": True,
                "updated_at": "2013-12-24T14:14:47.000000"}}},
    "zoneName": "nova"
})]


FAKE_SIMPLE_ZONES = [utils.FakeObject({
    "zoneState": {
        "available": True},
    "hosts": None,
    "zoneName": "nova"
})]


FAKE_FLAVORS = [utils.FakeObject({
    "name": "m1.small",
    "links": [],
    "ram": 2048,
    "OS-FLV-DISABLED:disabled": False,
    "vcpus": 1,
    "swap": "",
    "os-flavor-access:is_public": True,
    "rxtx_factor": 1.0,
    "OS-FLV-EXT-DATA:ephemeral": 0,
    "disk": 20,
    "id": "2"
}), utils.FakeObject({
    "name": "m1.large",
    "links": [],
    "ram": 8192,
    "OS-FLV-DISABLED:disabled": False,
    "vcpus": 4,
    "swap": "",
    "os-flavor-access:is_public": True,
    "rxtx_factor": 1.0,
    "OS-FLV-EXT-DATA:ephemeral": 870,
    "disk": 80,
    "id": "4"
})]


FAKE_SECURITY_GROUPS = [
    utils.FakeObject({
        "rules": [
            {
                "from_port": None,
                "ip_protocol": None,
                "to_port": None,
                "ip_range": {},
                "id": "3f8a140e-8d34-49c5-8cf2-5bec936b6c5c",
            },
            {
                "from_port": None,
                "ip_protocol": None,
                "to_port": None,
                "ip_range": {},
                "id": "9b0006c7-5e58-4b8e-a081-f0381c44bb2f",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "2cfdbf3a-0564-4b3b-bb85-00eb8d518f0c",
        "name": "default",
        "description": "default",
    }),
    utils.FakeObject({
        "rules": [
            {
                "from_port": 223,
                "ip_protocol": "udp",
                "to_port": 322,
                "ip_range": {"cidr": "55.0.0.0/24"},
                "id": "26f6c9e4-d8ca-4a96-b752-b848716f05f5",
            },
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {"cidr": "44.0.0.0/24"},
                "id": "4a2f2805-cde0-4515-9910-f2f8e77ba5f7",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "44.0.0.0/24"},
                "id": "e137dae4-ea4e-401d-8941-96a207e435b9",
            },
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {"cidr": "55.0.0.0/24"},
                "id": "e6a866a8-969a-41d9-b621-964a50f46381",
            },
            {
                "from_port": 223,
                "ip_protocol": "udp",
                "to_port": 322,
                "ip_range": {"cidr": "44.0.0.0/24"},
                "id": "f830670e-f90f-477f-9605-e871640cf8c2",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "55.0.0.0/24"},
                "id": "fbd2ada0-c5fc-4047-9558-2fb90874c8b3",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "a4ab9c5f-f0b5-4952-8e76-6a8ca0d0a402",
        "name": "fake-firewall-1",
        "description": "simple firewall",
    }),
    utils.FakeObject({
        "rules": [],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "c3859194-f111-4f24-b93b-095b056f38e2",
        "name": "fake-firewall-2",
        "description": "openstack sg w/o rules",
    }),
    utils.FakeObject({
        "rules": [
            {
                "from_port": 1000,
                "ip_protocol": "tcp",
                "to_port": 2000,
                "ip_range": {"cidr": "77.0.0.0/24"},
                "id": "01ecc4c4-41be-4af1-9a64-e2f866176001",
            },
            {
                "from_port": 1000,
                "ip_protocol": "tcp",
                "to_port": 2000,
                "ip_range": {},
                "id": "8709247a-afd8-4673-aac4-e22d8432a31e",
            },
            {
                "from_port": 1000,
                "ip_protocol": "tcp",
                "to_port": 2000,
                "ip_range": {"cidr": "78.0.0.0/24"},
                "id": "d67e8103-b32b-428b-bd20-8337b95456f1",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "b599598d-41b9-4075-a47e-019ba785c243",
        "name": "fake-firewall-3",
        "description": ("openstack sg with cidr & secgroup rules"),
    }),
    utils.FakeObject({
        "rules": [
            {
                "from_port": 5678,
                "ip_protocol": "tcp",
                "to_port": 5678,
                "ip_range": {"cidr": "66.0.0.0/24"},
                "id": "0642de5e-3c59-4c1c-8816-be6998c3c8a2",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "66.0.0.0/24"},
                "id": "b1a2b159-76e5-4baf-926a-a4ce09098377",
            },
            {
                "from_port": 1234,
                "ip_protocol": "tcp",
                "to_port": 1234,
                "ip_range": {"cidr": "88.0.0.0/24"},
                "id": "f7abbaab-f4fe-49fb-ac7f-bd8c49e60c61",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "fac84db7-aded-4152-a29e-5db00e052233",
        "name": "fake-firewall-4",
        "description": ("openstack sg too complex to translate into gce "
                        "rules"),
    }),
    utils.FakeObject({
        "rules": [
            {
                "from_port": 6666,
                "ip_protocol": "tcp",
                "to_port": 6666,
                "ip_range": {"cidr": "111.0.0.0/24"},
                "id": "634a199e-fb97-41d2-b12f-273c23a1c065"
            },
            {
                "from_port": 5555,
                "ip_protocol": "tcp",
                "to_port": 5555,
                "ip_range": {"cidr": "222.0.0.0/24"},
                "id": "bf34b3b0-29aa-4abf-a686-f29d9fb342d8"
            },
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {},
                "id": "fdf5dbe1-e824-46a6-a4d3-d2e37843a6d2"
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "03060521-fe0b-425f-bf33-d5061d58bae9",
        "name": "fake-firewall-5",
        "description": "openstack sg with combined & too complex rules",
    }),
    utils.FakeObject({
        "rules": [
            {
                "from_port": 0,
                "ip_protocol": "icmp",
                "to_port": 8,
                "ip_range": {"cidr": "100.0.0.0/24"},
                "id": "ae452a08-af3b-4d6a-b38e-2f4acad63331",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "d4c41e39-159c-4f96-8176-86c7b177880f",
        "name": "fake-firewall-6",
        "description": "openstack sg with too complex icmp rule",
    }),
    utils.FakeObject({
        "rules": [
            {
                "from_port": -1,
                "ip_protocol": "icmp",
                "to_port": -1,
                "ip_range": {"cidr": "110.0.0.0/24"},
                "id": "e2bc37af-529e-4ab3-8f41-358f3f9e62ab",
            },
        ],
        "project_id": "6678c02984ce4df8b26912db30481637",
        "id": "1aaa637b-87f4-4e27-bc86-ff63d30264b2",
        "name": "to-delete-firewall",
        "description": "firewall to delete test",
    }),
]


FAKE_INSTANCES = [{
    "OS-DCF:diskConfig": "MANUAL",
    "OS-EXT-AZ:availability_zone": "nova",
    "OS-EXT-SRV-ATTR:host": "apavlov-VirtualBox",
    "OS-EXT-SRV-ATTR:hypervisor_hostname": "apavlov-VirtualBox",
    "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
    "OS-EXT-STS:task_state": None,
    "OS-EXT-STS:vm_state": "active",
    "OS-EXT-STS:power_state": 1,
    "OS-SRV-USG:launched_at": "2013-08-14T13:46:23.000000",
    "OS-SRV-USG:terminated_at": None,
    "addresses": {
        "private": [{
            "OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:ea:ae:56",
            "version": 4,
            "addr": "10.0.1.3",
            "OS-EXT-IPS:type": "fixed"
        }, {
            "OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:ea:ae:56",
            "version": 4,
            "addr": "192.168.138.196",
            "OS-EXT-IPS:type": "floating"
        }]
    },
    "image": None,
    "flavor": {
        "id": "2",
    },
    "id": "d6957005-3ce7-4727-91d2-ae37fe5a199a",
    "security_groups": [{
        "name": "default"
    }],
    "name": "i1",
    "status": "ACTIVE",
    "created": "2013-08-14T13:45:32Z",
    "updated": "2013-08-14T13:46:23Z",
    "user_id": "0ed9ed7b2004443f802142ecf364738b",
    "accessIPv4": "",
    "accessIPv6": "",
    "progress": 0,
    "config_drive": "",
    "hostId": "cbf5e76abf66aa4363dbf17cfe0305093d903fe10389210856d85585",
    "key_name": "admin",
    "networks": {
        u'private': [u'10.0.1.3', u'192.168.138.196']
    },
    "tenant_id": fake_request.PROJECT_ID,
    "os-extended-volumes:volumes_attached": [{
        "id": "ab8829ad-eec1-44a2-8068-d7f00c53ee90"
    }],
    "metadata": {}
}, {
    "OS-DCF:diskConfig": "MANUAL",
    "OS-EXT-AZ:availability_zone": "nova",
    "OS-EXT-SRV-ATTR:host": "apavlov-VirtualBox",
    "OS-EXT-SRV-ATTR:hypervisor_hostname": "apavlov-VirtualBox",
    "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
    "OS-EXT-STS:task_state": None,
    "OS-EXT-STS:vm_state": "active",
    "OS-EXT-STS:power_state": 4,
    "OS-SRV-USG:terminated_at": None,
    "OS-SRV-USG:launched_at": "2013-08-14T13:47:11.000000",
    "addresses": {
        "default": [{
            "OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:ea:ae:50",
            "version": 4,
            "addr": "10.100.0.3",
            "OS-EXT-IPS:type": "fixed"
        }]
    },
    "image": {
        "id": "60ff30c2-64b6-4a97-9c17-322eebc8bd60",
    },
    "flavor": {
        "id": "4",
    },
    "id": "6472359b-d46b-4629-83a9-d2ec8d99468c",
    "security_groups": [{
        "name": "default"
    }],
    "name": "i2",
    "status": "SUSPENDED",
    "created": "2013-08-14T13:46:36Z",
    "updated": "2013-08-14T13:47:11Z",
    "user_id": "0ed9ed7b2004443f802142ecf364738b",
    "accessIPv4": "",
    "accessIPv6": "",
    "progress": 0,
    "config_drive": "",
    "hostId": "cbf5e76abf66aa4363dbf17cfe0305093d903fe10389210856d85585",
    "key_name": None,
    "networks": {
        "default": ["10.100.0.3"]
    },
    "tenant_id": fake_request.PROJECT_ID,
    "os-extended-volumes:volumes_attached": [],
    "metadata": {}
}]


FAKE_NEW_INSTANCE = {
    "OS-DCF:diskConfig": "MANUAL",
    "OS-EXT-AZ:availability_zone": "nova",
    "OS-EXT-SRV-ATTR:host": "apavlov-VirtualBox",
    "OS-EXT-SRV-ATTR:hypervisor_hostname": "apavlov-VirtualBox",
    "OS-EXT-SRV-ATTR:instance_name": "instance-00000003",
    "OS-EXT-STS:task_state": None,
    "OS-EXT-STS:vm_state": "active",
    "OS-EXT-STS:power_state": 1,
    "OS-SRV-USG:terminated_at": None,
    "OS-SRV-USG:launched_at": "2013-08-14T13:47:11.000000",
    "addresses": {
        "private": [{
            "OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:ea:ae:55",
            "version": 4,
            "addr": "10.100.0.4",
            "OS-EXT-IPS:type": "fixed"
        }]
    },
    "flavor": {
        "id": "4",
    },
    "id": "6472359b-3333-3333-3333-d2ec8d99468c",
    "security_groups": [{
        "name": "default"
    }],
    "name": "i2",
    "status": "ACTIVE",
    "created": "2013-08-14T13:46:36Z",
    "updated": "2013-08-14T13:47:11Z",
    "user_id": "0ed9ed7b2004443f802142ecf364738b",
    "accessIPv4": "",
    "accessIPv6": "",
    "progress": 0,
    "config_drive": "",
    "hostId": "cbf5e76abf66aa4363dbf17cfe0305093d903fe10389210856d85585",
    "key_name": None,
    "networks": {
        "default": ["10.100.0.3"]
    },
    "tenant_id": fake_request.PROJECT_ID,
    "os-extended-volumes:volumes_attached": [],
    "metadata": {}
}


FAKE_FLOATING_IPS = [utils.FakeObject({
    "instance_id": None,
    "ip": "192.168.138.195",
}), utils.FakeObject({
    "instance_id": "d6957005-3ce7-4727-91d2-ae37fe5a199a",
    "ip": "192.168.138.196",
})]


FAKE_LIMITS = utils.FakeObject({
    "rate": [],
    "human_id": None,
    "NAME_ATTR": "name",
    "HUMAN_ID": False,
    "absolute": [
        utils.FakeObject({"name": "maxServerMeta", "value": 128}),
        utils.FakeObject({"name": "maxPersonality", "value": 5}),
        utils.FakeObject({"name": "maxImageMeta", "value": 128}),
        utils.FakeObject({"name": "maxPersonalitySize", "value": 10240}),
        utils.FakeObject({"name": "maxTotalRAMSize", "value": 41000}),
        utils.FakeObject({"name": "maxSecurityGroupRules", "value": 20}),
        utils.FakeObject({"name": "maxTotalKeypairs", "value": 100}),
        utils.FakeObject({"name": "maxSecurityGroups", "value": 10}),
        utils.FakeObject({"name": "maxTotalFloatingIps", "value": 10}),
        utils.FakeObject({"name": "maxTotalInstances", "value": 10}),
        utils.FakeObject({"name": "maxTotalCores", "value": 17}),
        utils.FakeObject({"name": "totalRAMUsed", "value": 512}),
        utils.FakeObject({"name": "totalFloatingIpsUsed", "value": 3}),
        utils.FakeObject({"name": "totalInstancesUsed", "value": 4}),
        utils.FakeObject({"name": "totalSecurityGroupsUsed", "value": 2}),
        utils.FakeObject({"name": "totalCoresUsed", "value": 1}),
    ]
})


class FakeClassWithFind(object):
    def list(self):
        pass

    def find(self, **kwargs):
        matches = self.findall(**kwargs)
        num_matches = len(matches)
        if num_matches == 0:
            msg = "No %s matching %s." % (self.__class__.__name__, kwargs)
            raise novaclient.exceptions.NotFound(404, msg)
        elif num_matches > 1:
            raise novaclient.exceptions.NoUniqueMatch
        else:
            return matches[0]

    def findall(self, **kwargs):
        found = []
        searches = kwargs.items()

        detailed = True
        list_kwargs = {}

        list_argspec = inspect.getargspec(self.list)
        if "detailed" in list_argspec.args:
            detailed = ("human_id" not in kwargs and
                        "name" not in kwargs and
                        "display_name" not in kwargs)
            list_kwargs["detailed"] = detailed

        if "is_public" in list_argspec.args and "is_public" in kwargs:
            is_public = kwargs["is_public"]
            list_kwargs["is_public"] = is_public
            if is_public is None:
                tmp_kwargs = kwargs.copy()
                del tmp_kwargs["is_public"]
                searches = tmp_kwargs.items()

        listing = self.list(**list_kwargs)

        for obj in listing:
            try:
                if all(getattr(obj, attr) == value
                        for (attr, value) in searches):
                    if detailed:
                        found.append(obj)
                    else:
                        found.append(self.get(obj.id))
            except AttributeError:
                continue

        return found


class FakeAvailabilityZones(object):
    def list(self, detailed=True):
        if detailed:
            return FAKE_DETAILED_ZONES
        return FAKE_SIMPLE_ZONES


class FakeFlavors(FakeClassWithFind):
    def list(self, detailed=True, is_public=True):
        return FAKE_FLAVORS

    def get(self, flavor):
        flavor_id = utils.get_id(flavor)
        for flavor in FAKE_FLAVORS:
            if flavor.id == flavor_id:
                return flavor
        raise novaclient.exceptions.NotFound(
            novaclient.exceptions.NotFound.http_status)


class FakeKeypairs(object):
    def get(self, keypair):
        raise novaclient.exceptions.NotFound(
            novaclient.exceptions.NotFound.http_status)

    def create(self, name, public_key=None):
        pass

    def delete(self, key):
        raise novaclient.exceptions.NotFound(
            novaclient.exceptions.NotFound.http_status)

    def list(self):
        return []


class FakeServer(utils.FakeObject):

    _manager = None

    def __init__(self, manager, obj_dict):
        super(FakeServer, self).__init__(obj_dict)
        self._manager = manager

    def reboot(self, reboot_type):
        self._manager.reboot(self, reboot_type)

    def add_security_group(self, security_group):
        pass

    def remove_security_group(self, security_group):
        pass

    def delete(self):
        self._manager.delete(self)

    def add_floating_ip(self, address, fixed_address=None):
        pass

    def remove_floating_ip(self, address):
        pass


class FakeServers(object):
    _fake_instances = None

    def __init__(self):
        self._fake_instances = [FakeServer(self, i)
                           for i in FAKE_INSTANCES]

    def get(self, server):
        server_id = utils.get_id(server)
        for server in self._fake_instances:
            if server.id == server_id:
                return server
        raise novaclient.exceptions.NotFound(
            novaclient.exceptions.NotFound.http_status)

    def list(self, detailed=True, search_opts=None,
             marker=None, limit=None):
        result = self._fake_instances
        if search_opts and "name" in search_opts:
            name = search_opts["name"]
            result = [i for i in result if i.name == name]
        if search_opts and "fixed_ip" in search_opts:
            name = search_opts["fixed_ip"]
            filtered = []
            for i in result:
                for network in i.addresses:
                    for address in i.addresses[network]:
                        atype = address["OS-EXT-IPS:type"]
                        if atype == "fixed":
                            filtered.append(i)
                            break

            result = filtered

        return result

    def create(self, name, image, flavor, meta=None, files=None,
               reservation_id=None, min_count=None,
               max_count=None, security_groups=None, userdata=None,
               key_name=None, availability_zone=None,
               block_device_mapping=None, block_device_mapping_v2=None,
               nics=None, scheduler_hints=None,
               config_drive=None, disk_config=None, **kwargs):
        instance = copy.deepcopy(FakeServer(self, FAKE_NEW_INSTANCE))
        instance.name = name
        self._fake_instances.append(instance)
        return instance

    def add_floating_ip(self, server, address, fixed_address=None):
        self.get(server)

    def remove_floating_ip(self, server, address):
        self.get(server)

    def delete(self, server):
        self.get(server)

    def reboot(self, server, reboot_type):
        if reboot_type != "HARD":
            msg = _("Argument 'type' for reboot is not HARD or SOFT")
            raise novaclient.exceptions.BadRequest(message=msg)
        self.get(server)


class FakeSecurityGroups(FakeClassWithFind):
    _secgroups = FAKE_SECURITY_GROUPS

    def list(self):
        return self._secgroups

    def get(self, sg_id):
        secgroup = next((secgroup
                         for secgroup in self._secgroups
                         if secgroup.id == sg_id), None)
        if secgroup is None:
            raise novaclient.exceptions.NotFound(
                    404, "Security group %s not found" % sg_id)
        return secgroup

    def create(self, name, description):
        secgroup = utils.FakeObject({
            "name": name,
            "description": description,
            "rules": [],
            "project_id": "6678c02984ce4df8b26912db30481637",
            "id": "5707a6f0-799d-4739-8740-3efc73f122aa",
        })
        self._secgroups = copy.deepcopy(self._secgroups)
        self._secgroups.append(secgroup)
        return secgroup

    def delete(self, security_group):
        pass

    def add_rule(self, sg_id, ip_protocol, from_port, to_port, cidr):
        secgroup = self.get(sg_id)
        rule = {
            "id": uuid.uuid4(),
            "ip_protocol": ip_protocol,
            "from_port": from_port,
            "to_port": to_port,
            "ip_range": {"cidr": cidr},
        }
        secgroup.rules.append(rule)


class FakeSecurityGroupRules(object):
    def __init__(self, nova_client):
        self.security_groups = nova_client.security_groups

    def create(self, sg_id, ip_protocol, from_port, to_port, cidr):
        self.security_groups.add_rule(sg_id, ip_protocol, from_port,
                                      to_port, cidr)


class FakeFloatingIps(object):
    def list(self):
        return FAKE_FLOATING_IPS


class FakeLimits(object):
    def get(self, tenant_id):
        return FAKE_LIMITS


class FakeVolumes(object):
    def get_server_volumes(self, instance_id):
        return []

    def create_server_volume(self, instance_id, volume_id, device):
        instance = FakeServers().get(instance_id)
        volumes = getattr(instance, "os-extended-volumes:volumes_attached")
        volumes = [v["id"] for v in volumes]
        if volume_id in volumes:
            raise novaclient.exceptions.NotFound(
                novaclient.exceptions.NotFound.http_status)

    def delete_server_volume(self, instance_id, volume_id):
        instance = FakeServers().get(instance_id)
        volumes = getattr(instance, "os-extended-volumes:volumes_attached")
        volumes = [v["id"] for v in volumes]
        if volume_id not in volumes:
            raise novaclient.exceptions.NotFound(
                novaclient.exceptions.NotFound.http_status)


class FakeNovaClient(object):

    KIND = "fake_novaclient"
    __metaclass__ = base_api.Singleton

    def __init__(self, version, *args, **kwargs):
        self._servers = None
        self._security_group = None

    @property
    def client(self):
        return self

    @property
    def availability_zones(self):
        return FakeAvailabilityZones()

    @property
    def flavors(self):
        return FakeFlavors()

    @property
    def keypairs(self):
        return FakeKeypairs()

    @property
    def servers(self):
        if self._servers is None:
            self._servers = FakeServers()
        return self._servers

    @property
    def security_groups(self):
        if self._security_group is None:
            self._security_group = FakeSecurityGroups()
        return self._security_group

    @property
    def security_group_rules(self):
        return FakeSecurityGroupRules(self)

    @property
    def floating_ips(self):
        return FakeFloatingIps()

    @property
    def limits(self):
        return FakeLimits()

    @property
    def volumes(self):
        return FakeVolumes()


def fake_discover_extensions(self, version):
    return list()
