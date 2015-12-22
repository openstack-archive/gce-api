# Copyright 2010 United States Government as represented by the
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

import itertools
import netaddr
import testtools

from oslo_log import log as logging
from tempest.common.utils import data_utils
from tempest import config

from gceapi.tests.functional import base as base_gce


CONF = config.CONF
LOG = logging.getLogger("tempest.thirdparty.gce")

PUBLIC_KEY = ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCiU5kpbgCLrKxP1LYH9"
              "dumtf8d6Rb+CX/6irKYyJNbsNYSX1skM9jur17TiFlXQFCjorNYXZ/A1e"
              "EKbiDcZUKrINhibQfQlAJZpYP1isLUwJlUhJtGFFBW38wTuyG0MFBO+TF"
              "RtAG8GQRRfGDxIXvwUxuDR8sClNuTc0MURTbLCJGPFaK2S99NElNYP7R0"
              "QpzQyTHkfl492NKD9Zr7kjvnssqihuQ8dZ0dh5xE2RuF9VChdmmPmsfQG"
              "qtRXS6xf1Dy0rPHilEcJpGevcUs/JcqEnUd455uugfdueHLqhOvUt3WJU"
              "6mThQ28kTAe7nN17Pj3yKRyurF42bigVKNBudD GCE API testing")

PRIVATE_KEY = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "MIIEogIBAAKCAQEAolOZKW4Ai6ysT9S2B/XbprX/HekW/gl/+oqymMiTW7DWEl9b\n"
    "JDPY7q9e04hZV0BQo6KzWF2fwNXhCm4g3GVCqyDYYm0H0JQCWaWD9YrC1MCZVISb\n"
    "RhRQVt/ME7shtDBQTvkxUbQBvBkEUXxg8SF78FMbg0fLApTbk3NDFEU2ywiRjxWi\n"
    "tkvfTRJTWD+0dEKc0Mkx5H5ePdjSg/Wa+5I757LKoobkPHWdHYecRNkbhfVQoXZp\n"
    "j5rH0BqrUV0usX9Q8tKzx4pRHCaRnr3FLPyXKhJ1HeOebroH3bnhy6oTr1Ld1iVO\n"
    "pk4UNvJEwHu5zdez498ikcrqxeNm4oFSjQbnQwIDAQABAoIBAG0MkjlF3/H1V3Dt\n"
    "6jfgz+XoH/H9E+gng6VRpfeDz5LqcnW3P6hLeHGouKCM2dAGseWsOKWlh9vpExyJ\n"
    "rWPCVw5Vq2g77OMPe6Cz07mRtZ9tn9QqnZFvtiUWhae/sD23s0vKlnpX3k550+/W\n"
    "Cd4T64ogmrwP7+7VB8m/xhGJCe1My2j3bziloNo/3hmmZQPjgSAVn8sDLCmRGt84\n"
    "TYO/f4yY9ftGsWZEa0GhtixBGs9YviyuHz1ANyTGJg6VJ/GIwaK/sefD22MGKWTN\n"
    "AMuVdPThDwGftcL6Apd44yiiIbm5ufD7w2ZS2l9/dG+0RXV+iSTXQZlNn6MHo3zw\n"
    "ebc+m6ECgYEAzqImO6hyKAEnWFgXc/NgLk4xxdumEbn3FqVqeTKlJTuUGqiAVzfD\n"
    "+UDswIvRKwxGnJXlNTMwkT6w9LeFC5W7xvnr4a2YFj68oDNY4Gi6CFcv3kG7/6MR\n"
    "u9bLtxDh3Q4JHwhLO5cWejIdZ4P+9aG7GzUTqofPMmXEEaiiam7NonMCgYEAyRuc\n"
    "J1TOm3B/zy29rYgY8BLgdEsdQN07v1JA1xcNG6A24mxBbPrkOuDrZ0kLtnFewVFG\n"
    "4fLEO5MQBhsRKHK0pw3VE5azO8jHyFzccEjuObUeuYXSLxZFmK8jdcIkRirh6O7D\n"
    "qCm/cEePnkxIFEIjMrctWXxa/jYEZYheRCXH4/ECgYB0PfvMK+KsZpm/tS7cZ9l/\n"
    "szWE3R/7cOZzsvLG45rL60xSAuDQL+rrWX7WgtFUqj8+74RV/UohK2dZA7Sw47cT\n"
    "JJ1yA7o/KWPrq3cgJ0ogTwv6uHgOQ6pCRX+sqK6nMLIo5v2LtF9Mtsyb40GW5Tjh\n"
    "AWbi1CvXajB2zqsvvM2pyQKBgG6dSBt+ExH+I96BqzWaiRTrXRe6BQIbbXSDOnTU\n"
    "Efqi+e06XBYkPYqBEhnCXLXhz5uHJ/S5geO+tO6Wzq4vwVutSQi4OCdm/TQgl4MP\n"
    "KjEFhTvH9l694lPj6R4pRahuh8mGIooJRGnugnkwPekeo5uOk1wIAUiXz31FL4xO\n"
    "N48RAoGAK7+20dPiStPo8dnFrYjQ2j5xuMO2/0+BaLFhDWTiHHjALCWOHkXJ1JtN\n"
    "9LM2cIlCC79p4+7KQwUXvMBcnAx6qwTMHisGg3WfxlD8f7MuDDR+or1fd/c0byti\n"
    "z1r/I9Ya6/bAXQOjruxpHkECZl5DEdVvT0E2qL/pQx0rfqnkdfE=\n"
    "-----END RSA PRIVATE KEY-----\n")


class GCEScenarioContext(object):
    zone = None
    region = None
    machine_type = None
    image_name = None
    image = None
    boot_disk_name = None
    boot_disk = None
    empty_disk_name = None
    empty_disk = None
    network_name = None
    network_cidr = None
    gateway_ip = None
    network = None
    firewall_name = None
    instance_name = None
    instance = None
    address_name = None
    address = None
    access_config_name = None


class TestGCEScenario(base_gce.GCESmokeTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestGCEScenario, cls).setUpClass()
        cls.ctx = GCEScenarioContext()

    @classmethod
    def tearDownClass(cls):
        super(TestGCEScenario, cls).tearDownClass()

    def setUp(self):
        super(TestGCEScenario, self).setUp()

    @base_gce.GCESmokeTestCase.incremental
    def test_000_get_zone(self):
        (status, body) = self.gce.get("/zones")
        self.assertEqual(200, status, message=body.get("message"))
        self.ctx.zone = next(itertools.ifilter(lambda x: x["status"] == "UP",
                                               body["items"]),
                             None)
        self.assertIsNotNone(self.ctx.zone)
        self.gce.set_zone(self.ctx.zone["name"])

    @base_gce.GCESmokeTestCase.incremental
    def test_001_get_region(self):
        (status, body) = self.gce.get("/regions")
        self.assertEqual(200, status, message=body.get("message"))
        self.ctx.region = next(itertools.ifilter(lambda x: x["status"] == "UP",
                                                 body["items"]),
                             None)
        self.assertIsNotNone(self.ctx.region)
        self.gce.set_region(self.ctx.region["name"])

    @base_gce.GCESmokeTestCase.incremental
    def test_002_get_machine_type(self):
        (status, body) = self.gce.zone_get("/machineTypes")
        self.assertEqual(200, status, message=body.get("message"))
        machine_types = body.get("items")
        self.assertTrue(machine_types)
        if CONF.gceapi.machine_type:
            self.ctx.machine_type = next(
                t for t in machine_types
                if t["name"] == CONF.gceapi.machine_type)
        else:
            self.ctx.machine_type = min(machine_types,
                                        key=lambda x: x["memoryMb"])

    @base_gce.GCESmokeTestCase.incremental
    def test_003_get_project(self):
        (status, body) = self.gce.get("")
        self.assertEqual(200, status, message=body.get("message"))

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        not CONF.gceapi["existing_image"],
        "Skipped by config settings")
    def test_010_get_image(self):
        (status, body) = self.gce.get("/global/images",
                                      CONF.gceapi.existing_image)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertIsNotNone(body)
        self.ctx.image = body

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["existing_image"],
        "Skipped by config settings")
    def test_011_create_image(self):
        self.ctx.image_name = data_utils.rand_name("image-")
        (status, body) = self.gce.post(
            "/global/images",
            body={
                "name": self.ctx.image_name,
                "rawDisk": {
                    "source": CONF.gceapi.http_raw_image,
                },
                "sourceType": "RAW",
            })
        self.assertEqual(200, status, message=body.get("message"))
        self.add_resource_cleanup(body["targetLink"])
        self.verify_resource_uri(body["targetLink"], "/global/images",
            self.ctx.image_name)
        self.wait_for_operation(body, "insert", "READY")

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["existing_image"],
        "Skipped by config settings")
    def test_012_check_image_info(self):
        (status, body) = self.gce.get("/global/images", self.ctx.image_name)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertEqual(self.ctx.image_name, body["name"])
        self.assertEqual("READY", body["status"])
        self.assertEqual("RAW", body["sourceType"])
        self.verify_resource_uri(body["selfLink"], "/global/images",
                                 self.ctx.image_name)
        self.ctx.image = body

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["skip_bootable_volume"],
        "Skipped by config settings")
    def test_020_create_bootable_disk(self):
        self.ctx.boot_disk_name = data_utils.rand_name("boot-disk-")
        (status, body) = self.gce.zone_post(
            "/disks",
            params={
                "sourceImage": self.ctx.image["selfLink"],
            },
            body={
                "name": self.ctx.boot_disk_name,
            })
        self.assertEqual(200, status, message=body.get("message"))
        self.add_resource_cleanup(body["targetLink"])
        self.verify_zone_resource_uri(body["targetLink"], "/disks",
            self.ctx.boot_disk_name)
        self.wait_for_operation(body, "insert", "READY")

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["skip_bootable_volume"],
        "Skipped by config settings")
    def test_021_check_bootable_disk_info(self):
        (status, body) = self.gce.zone_get("/disks/", self.ctx.boot_disk_name)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertEqual(self.ctx.boot_disk_name, body["name"])
        self.assertIsNone(body["description"])
        self.assertEqual("READY", body["status"])
        self.verify_zone_resource_uri(body["selfLink"], "/disks",
                                      self.ctx.boot_disk_name)
        self.ctx.boot_disk = body

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["skip_empty_volume"],
        "Skipped by config settings")
    def test_022_create_empty_disk(self):
        self.ctx.empty_disk_name = data_utils.rand_name("empty-disk-")
        (status, body) = self.gce.zone_post(
            "/disks",
            body={
                "name": self.ctx.empty_disk_name,
                "sizeGb": 1,
                "description": "test empty volume",
            })
        self.assertEqual(200, status, message=body.get("message"))
        self.add_resource_cleanup(body["targetLink"])
        self.verify_zone_resource_uri(body["targetLink"], "/disks",
            self.ctx.empty_disk_name)
        self.wait_for_operation(body, "insert", "READY")

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["skip_empty_volume"],
        "Skipped by config settings")
    def test_023_check_empty_disk_info(self):
        (status, body) = self.gce.zone_get("/disks/", self.ctx.empty_disk_name)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertEqual(self.ctx.empty_disk_name, body["name"])
        self.assertEqual("test empty volume", body["description"])
        self.assertEqual("READY", body["status"])
        self.assertEqual(1, body["sizeGb"])
        self.verify_zone_resource_uri(body["selfLink"], "/disks",
                                      self.ctx.empty_disk_name)
        self.ctx.empty_disk = body

    @base_gce.GCESmokeTestCase.incremental
    def test_030_create_network(self):
        self.ctx.network_name = data_utils.rand_name("network-")
        cfg = CONF.network
        network_cidr = netaddr.IPNetwork(cfg.tenant_network_cidr)
        subnet_cidr = next(s for s in network_cidr.
                           subnet(cfg.tenant_network_mask_bits))
        gateway_ip = netaddr.IPAddress(subnet_cidr.last - 1)
        self.ctx.network_cidr = str(subnet_cidr)
        self.ctx.gateway_ip = str(gateway_ip)
        (status, body) = self.gce.post(
            "/global/networks",
            body={
                "name": self.ctx.network_name,
                "IPv4Range": self.ctx.network_cidr,
                "gatewayIPv4": self.ctx.gateway_ip,
            })
        self.assertEqual(200, status, message=body.get("message"))
        self.add_resource_cleanup(body["targetLink"])
        self.verify_resource_uri(body["targetLink"], "/global/networks",
            self.ctx.network_name)
        self.wait_for_operation(body, "insert", None)

    @base_gce.GCESmokeTestCase.incremental
    def test_031_check_network_info(self):
        (status, body) = self.gce.get("/global/networks",
                                      self.ctx.network_name)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertEqual(self.ctx.network_name, body["name"])
        self.assertEqual(self.ctx.network_cidr, body["IPv4Range"])
        self.assertEqual(self.ctx.gateway_ip, body["gatewayIPv4"])
        self.verify_resource_uri(body["selfLink"], "/global/networks",
                                 self.ctx.network_name)
        self.ctx.network = body

    @base_gce.GCESmokeTestCase.incremental
    def test_040_create_firewall(self):
        self.ctx.firewall_name = data_utils.rand_name("firewall-")
        (status, body) = self.gce.post(
            "/global/firewalls",
            body={
                "name": self.ctx.firewall_name,
                "description": "test firewall",
                "network": self.ctx.network["selfLink"],
                "sourceRanges": ["0.0.0.0/0"],
                "allowed": [
                    {"IPProtocol": "icmp"},
                    {
                        "IPProtocol": "tcp",
                        "ports": ["22", "80", "8080-8089"],
                    },
                ],
            })
        self.assertEqual(200, status, message=body.get("message"))
        self.add_resource_cleanup(body["targetLink"])
        self.verify_resource_uri(body["targetLink"], "/global/firewalls",
            self.ctx.firewall_name)
        self.wait_for_operation(body, "insert", None)

    @base_gce.GCESmokeTestCase.incremental
    def test_041_check_firewall_info(self):
        (status, body) = self.gce.get("/global/firewalls",
                                      self.ctx.firewall_name)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertEqual(self.ctx.firewall_name, body["name"])
        self.assertTrue(body["description"].startswith("test firewall"))
        self.assertEqual(body["network"], self.ctx.network["selfLink"])
        self.assertEqual(body["sourceRanges"], ["0.0.0.0/0"])
        self.assertEqual(2, len(body["allowed"]))
        self.assertIn({"IPProtocol": "icmp"}, body["allowed"])
        tcp_range = next((x for x in body["allowed"]
                          if x["IPProtocol"] == "tcp"), None)
        self.assertIsNotNone(tcp_range)
        self.assertItemsEqual(["22", "80", "8080-8089"], tcp_range["ports"])
        self.verify_resource_uri(body["selfLink"], "/global/firewalls",
                                 self.ctx.firewall_name)

    @base_gce.GCESmokeTestCase.incremental
    def test_050_run_instance(self):
        self.ctx.instance_name = data_utils.rand_name("instance-")
        disks = []
        if not CONF.gceapi.skip_bootable_volume:
            disks.append({
                "kind": self.ctx.boot_disk["kind"],
                "type": "PERSISTENT",
                "mode": "READ_WRITE",
                "source": self.ctx.boot_disk["selfLink"],
                "deviceName": "vda",
                "boot": True,
            })
        if not CONF.gceapi.skip_empty_volume:
            disks.append({
                "kind": self.ctx.empty_disk["kind"],
                "type": "PERSISTENT",
                "mode": "READ_WRITE",
                "source": self.ctx.empty_disk["selfLink"],
                "deviceName": "vdb",
                "boot": False,
            })
        body = {
            "name": self.ctx.instance_name,
            "description": "test instance",
            "machineType": self.ctx.machine_type["selfLink"],
            "disks": disks,
            "metadata": {
                "items": [
                    {
                        "key": "sshKeys",
                        "value": ":".join([data_utils.rand_name("keypair-"),
                                           PUBLIC_KEY])
                    },
                ],
            },
            "networkInterfaces": [{
                "network": self.ctx.network["selfLink"],
            }],
            "tags": {
                "items": [],
            },
        }
        if CONF.gceapi.skip_bootable_volume:
            body["image"] = self.ctx.image["selfLink"]
        (status, body) = self.gce.zone_post("/instances", body=body)
        self.assertEqual(200, status, message=body.get("message"))
        self.add_resource_cleanup(body["targetLink"])
        self.verify_zone_resource_uri(body["targetLink"], "/instances",
            self.ctx.instance_name)
        self.wait_for_operation(body, "insert", "RUNNING")

    @base_gce.GCESmokeTestCase.incremental
    def test_051_check_instance_info(self):
        (status, body) = self.gce.zone_get("/instances/",
                                           self.ctx.instance_name)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertEqual(self.ctx.instance_name, body["name"])
        self.assertEqual("test instance", body["description"])
        self.assertEqual("RUNNING", body["status"])
        self.assertEqual("ACTIVE", body["statusMessage"])
        self.assertEqual(self.ctx.machine_type["selfLink"],
                         body["machineType"])
        nwifs = body.get("networkInterfaces")
        self.assertEqual(1, len(nwifs))
        nwif = nwifs[0]
        try:
            self.assertEqual(self.ctx.network_name, nwif["name"])
        except Exception:
            LOG.exception("Is nova network here?")
            # NOTE(apavlov): change network name for future usage in this case
            self.ctx.network_name = nwif["name"]

        cidrs = netaddr.all_matching_cidrs(nwif["networkIP"],
                                           [self.ctx.network_cidr])
        try:
            self.assertEqual(1, len(cidrs))
        except Exception:
            LOG.exception("Is nova network here?")

        try:
            self.assertEqual(self.ctx.network_cidr, str(cidrs[0]))
        except Exception:
            LOG.exception("Is nova network here?")

        self.verify_zone_resource_uri(body["selfLink"], "/instances",
                                      self.ctx.instance_name)
        self.ctx.instance = body

    @testtools.skipIf(
        not CONF.gceapi["use_floatingip"],
        "Skipped by config settings")
    @base_gce.GCESmokeTestCase.incremental
    def test_060_reserve_address(self):
        self.ctx.address_name = data_utils.rand_name("address-")
        (status, body) = self.gce.region_post(
            "/addresses",
            body={
                "name": self.ctx.address_name,
                "description": "test address",
            })
        self.assertEqual(200, status, message=body.get("message"))
        self.add_resource_cleanup(body["targetLink"])
        self.verify_region_resource_uri(body["targetLink"], "/addresses",
            self.ctx.address_name)
        self.wait_for_operation(body, "insert", "RESERVED")

    @testtools.skipIf(
        not CONF.gceapi["use_floatingip"],
        "Skipped by config settings")
    @base_gce.GCESmokeTestCase.incremental
    def test_061_check_address_info(self):
        (status, body) = self.gce.region_get("/addresses/",
                                             self.ctx.address_name)
        self.assertEqual(200, status, message=body.get("message"))
        self.assertEqual(self.ctx.address_name, body["name"])
        self.assertEqual("test address", body["description"])
        self.assertEqual("RESERVED", body["status"])
        self.assertIsNotNone(body["address"])

        self.verify_region_resource_uri(body["selfLink"], "/addresses",
                                      self.ctx.address_name)
        self.ctx.address = body

    @testtools.skipIf(
        not CONF.gceapi["use_floatingip"],
        "Skipped by config settings")
    @base_gce.GCESmokeTestCase.incremental
    def test_062_associate_floating_ip(self):
        self.ctx.access_config_name = data_utils.rand_name("accessConfig-")
        (status, body) = self.gce.zone_post(
            "/instances",
            self.ctx.instance_name,
            "addAccessConfig",
            params={
                "networkInterface": self.ctx.network_name,
            },
            body={
                "type": "ONE_TO_ONE_NAT",
                "name": self.ctx.access_config_name,
                "natIP": self.ctx.address["address"]
            })
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "addAccessConfig", "RUNNING")

    @testtools.skipIf(
        not CONF.gceapi["use_floatingip"],
        "Skipped by config settings")
    @base_gce.GCESmokeTestCase.incremental
    def test_063_get_floating_ip_info(self):
        (status, body) = self.gce.zone_get("/instances/",
                                           self.ctx.instance_name)
        self.assertEqual(200, status, message=body.get("message"))
        nwifs = body.get("networkInterfaces")
        self.assertEqual(1, len(nwifs))
        nwif = nwifs[0]
        fp_infs = nwif.get("accessConfigs")
        self.assertEqual(1, len(fp_infs))
        fp_inf = fp_infs[0]
        self.assertEqual("ONE_TO_ONE_NAT", fp_inf["type"])
        self.assertEqual(self.ctx.access_config_name, fp_inf["name"])
        self.assertEqual(self.ctx.address["address"], fp_inf["natIP"])
        self.ctx.instance = body

    @base_gce.GCESmokeTestCase.incremental
    def test_064_ping_instance(self):
        for network_interface in self.ctx.instance["networkInterfaces"]:
            ip = self._get_ip_address(network_interface)
            self._ping_ip_address(ip)

    @base_gce.GCESmokeTestCase.incremental
    def test_065_ssh_instance(self):
        for network_interface in self.ctx.instance["networkInterfaces"]:
            ip = self._get_ip_address(network_interface)
            self._check_ssh_connectivity(ip,
                                         CONF.gceapi.image_username,
                                         PRIVATE_KEY)

    @base_gce.GCESmokeTestCase.incremental
    def test_100_reset_instance(self):
        (status, body) = self.gce.zone_post("/instances",
                                            self.ctx.instance_name,
                                            "reset")
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "reset", "RUNNING")

    @base_gce.GCESmokeTestCase.incremental
    def test_101_ping_reseted_instance(self):
        for network_interface in self.ctx.instance["networkInterfaces"]:
            ip = self._get_ip_address(network_interface)
            self._ping_ip_address(ip)

    @base_gce.GCESmokeTestCase.incremental
    def test_900_stop_instance(self):
        instance_link = self.ctx.instance["selfLink"]
        self.cancel_resource_cleanup(instance_link)
        (status, body) = self.gce.delete(instance_link)
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "delete", None)
        self.ctx.instance = None

    @testtools.skipIf(
        not CONF.gceapi["use_floatingip"],
        "Skipped by config settings")
    @base_gce.GCESmokeTestCase.incremental
    def test_901_release_address(self):
        address_link = self.ctx.address["selfLink"]
        self.cancel_resource_cleanup(address_link)
        (status, body) = self.gce.delete(address_link)
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "delete", None)
        self.ctx.address = None

    @base_gce.GCESmokeTestCase.incremental
    def test_910_delete_network(self):
        network_link = self.ctx.network["selfLink"]
        self.cancel_resource_cleanup(network_link)
        (status, body) = self.gce.delete(network_link)
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "delete", None)
        self.ctx.network = None

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["skip_empty_volume"],
        "Skipped by config settings")
    def test_920_delete_empty_disk(self):
        disk_link = self.ctx.empty_disk["selfLink"]
        self.cancel_resource_cleanup(disk_link)
        (status, body) = self.gce.delete(disk_link)
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "delete", None)
        self.ctx.empty_disk = None

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["skip_bootable_volume"],
        "Skipped by config settings")
    def test_921_delete_bootable_disk(self):
        disk_link = self.ctx.boot_disk["selfLink"]
        self.cancel_resource_cleanup(disk_link)
        (status, body) = self.gce.delete(disk_link)
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "delete", None)
        self.ctx.boot_disk = None

    @base_gce.GCESmokeTestCase.incremental
    @testtools.skipIf(
        CONF.gceapi["existing_image"],
        "Skipped by config settings")
    def test_922_delete_image(self):
        image_link = self.ctx.image["selfLink"]
        self.cancel_resource_cleanup(image_link)
        (status, body) = self.gce.delete(image_link)
        self.assertEqual(200, status, message=body.get("message"))
        self.wait_for_operation(body, "delete", None)
        self.ctx.image = None
