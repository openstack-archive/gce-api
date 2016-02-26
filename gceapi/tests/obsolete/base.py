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

import json
import subprocess
import unittest
import urlparse

from oslo_log import log as logging
from tempest.lib.common import rest_client
import testtools

from tempest.common.utils.linux import remote_client
from tempest import config
from tempest import exceptions
from tempest import manager
import tempest.test

CONF = config.CONF
LOG = logging.getLogger("tempest.thirdparty.gce")
REGION_NAME = 'region-one'


class GCEConnection(rest_client.RestClient):

    def __init__(self, auth_provider):
        super(GCEConnection, self).__init__(auth_provider,
                                            "gceapi", REGION_NAME)
        self.service = CONF.gceapi.catalog_type

    def set_zone(self, zone):
        self.zone = zone

    def set_region(self, region):
        self.region = region

    def auth_request(self, uri, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['AUTHORIZATION'] = "a " + self.token
        return self.http_obj.request(uri, **kwargs)

    def _combine_uri(self, *path):
        if not len(path):
            return None

        parts = []
        gce_cfg = CONF.gceapi
        if not urlparse.urlsplit(path[0]).netloc:
            parts = [self.base_url, gce_cfg.api_path, self.tenant_name]
        parts.extend(path)
        uri = "/".join(x.strip("/") for x in parts if x)
        return uri

    def _add_params(self, uri, params):
        if not params:
            return uri
        param_list = ["%s=%s" % (param, value)
                      for (param, value) in params.iteritems()]
        return "%s?%s" % (uri, ";".join(param_list))

    def _convert_response(self, response):
        header = response[0]
        body = (json.loads(response[1])
                if header.get("content-type") == "application/json"
                else None)
        return (header.status, body)

    def request(self, *path, **kwargs):
        if (self.token is None) or (self.base_url is None):
            self._set_auth()

        uri = self._combine_uri(*path)
        params = kwargs.pop("params", None)
        uri = self._add_params(uri, params)
        response = self.auth_request(uri, **kwargs)
        return self._convert_response(response)

    def _add_zone_path(self, *path):
        return ('zones', self.zone) + path

    def _add_region_path(self, *path):
        return ('regions', self.region) + path

    def get(self, *path):
        return self.request(*path)

    def zone_get(self, *path):
        return self.get(*self._add_zone_path(*path))

    def region_get(self, *path):
        return self.get(*self._add_region_path(*path))

    def post(self, *path, **kwargs):
        req_args = {"method": "POST"}
        if "body" in kwargs:
            req_args["body"] = json.dumps(kwargs["body"])
            req_args["headers"] = {"Content-Type": "application/json"}
        if "params" in kwargs:
            req_args["params"] = kwargs["params"]
        return self.request(*path, **req_args)

    def zone_post(self, *path, **kwargs):
        return self.post(*self._add_zone_path(*path), **kwargs)

    def region_post(self, *path, **kwargs):
        return self.post(*self._add_region_path(*path), **kwargs)

    def delete(self, *path):
        return self.request(*path, method="DELETE")

    def zone_delete(self, *path):
        return self.delete(*self._add_zone_path(*path))


class GCESmokeTestCase(testtools.TestCase):
    failed = False

    @classmethod
    def setUpClass(cls):
        super(GCESmokeTestCase, cls).setUpClass()
        cls.gce = GCEConnection(manager.Manager().auth_provider)
        cls._trash_bin = []

    @classmethod
    def tearDownClass(cls):
        targetLink = None
        opLink = None

        def check():
            (status, body) = cls.gce.get(opLink)
            if status == 200 and body.get("progress") == 100:
                return True
            return False

        timeout = CONF.gceapi.operation_timeout
        idle = CONF.gceapi.operation_interval
        while cls._trash_bin:
            targetLink = cls._trash_bin.pop()
            (status, body) = cls.gce.delete(targetLink)
            if status != 200:
                msg = ("Delete operation fails for resource %s"
                    % targetLink)
                LOG.error(msg)
                continue

            try:
                opLink = body["selfLink"]
                result = tempest.test.call_until_true(check, timeout, idle)
                if not result:
                    msg = ("Timed out waiting for deletion resource %s"
                        % targetLink)
                    LOG.error(msg)
            except Exception as exc:
                LOG.exception(exc)

    @classmethod
    def add_resource_cleanup(cls, resource_link):
        if resource_link not in cls._trash_bin:
            cls._trash_bin.append(resource_link)

    @classmethod
    def cancel_resource_cleanup(cls, resource_link):
        if resource_link in cls._trash_bin:
            cls._trash_bin.remove(resource_link)

    @staticmethod
    def incremental(meth):
        def decorator(*args, **kwargs):
            try:
                meth(*args, **kwargs)
            except unittest.SkipTest:
                raise
            except Exception:
                GCESmokeTestCase.failed = True
                raise
        decorator.__test__ = True
        return decorator

    def setUp(self):
        if GCESmokeTestCase.failed:
            raise unittest.SkipTest("Skipped by previous exception")
        super(GCESmokeTestCase, self).setUp()
        self.skipTest('Not to run in gating. It is just an old example and '
                      'will be remove removed in future')

    def wait_for_operation(self, body, operation, status):
        self.assertEqual("compute#operation", body["kind"])
        self.assertEqual(operation, body["operationType"])
        targetLink = body["targetLink"]
        opLink = body["selfLink"]

        def check():
            (http_status, op_body) = self.gce.get(opLink)
            self.assertEqual(http_status, 200)
            self.assertEqual(targetLink, op_body["targetLink"])
            self.assertEqual(opLink, op_body["selfLink"])

            error = op_body.get("error")
            if error:
                msg = "Operation(resource %s) error %s (%s)" % (targetLink,
                    error["errors"], op_body.get("httpErrorMessage"))
                self.fail(msg)

            if op_body["progress"] != 100:
                return False
            self.assertEqual("DONE", op_body["status"])
            return True

        timeout = CONF.gceapi.operation_timeout
        idle = CONF.gceapi.operation_interval
        result = tempest.test.call_until_true(check, timeout, idle)
        if not result:
            message = "Timed out waiting for uri %s" % targetLink
            raise exceptions.TimeoutException(message)

        (http_status, body) = self.gce.get(targetLink)
        # NOTE(apavlov): only for delete* we wait 404. for other 200
        target_status = 404 if "delete" in operation else 200
        self.assertEqual(http_status, target_status)

        if status:
            self.assertEqual(status, body["status"])

    def verify_resource_uri(self, uri, resource_path=None, resource_name=None):
        (scheme, netloc, path, query, fragment) = urlparse.urlsplit(str(uri))
        self.assertEqual(self.gce.base_url.strip("/"),
                         scheme + "://" + netloc)
        resource_parts = [CONF.gceapi.api_path.strip("/"),
                          self.gce.tenant_name]
        if resource_path is not None:
            resource_parts.append(resource_path.strip("/"))
        if resource_name is not None:
            resource_parts.append(resource_name)

        self.assertEqual("/" + "/".join(resource_parts), path)
        self.assertFalse(query)
        self.assertFalse(fragment)

    def verify_region_resource_uri(self, uri, resource_path, resource_name):
        resource_path = "/".join(["regions", self.ctx.region["name"],
                                  resource_path.strip("/")])
        self.verify_resource_uri(uri, resource_path, resource_name)

    def verify_zone_resource_uri(self, uri, resource_path, resource_name):
        resource_path = "/".join(["zones", self.ctx.zone["name"],
                                  resource_path.strip("/")])
        self.verify_resource_uri(uri, resource_path, resource_name)

    def _get_ip_address(self, network_interface):
        if CONF.gceapi.use_floatingip:
            ipaddr = network_interface["accessConfigs"][0]["natIP"]
        else:
            ipaddr = network_interface["networkIP"]
        return ipaddr

    def _ping_ip_address(self, ip_address):
        cmd = ['ping', '-c1', '-w1', ip_address]

        def ping():
            proc = subprocess.Popen(cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
            return True if proc.returncode == 0 else False

        result = tempest.test.call_until_true(
            ping, CONF.compute.ping_timeout, 1)
        if result:
            return

        message = "Timed out waiting for ping %s" % (ip_address)
        raise exceptions.TimeoutException(message)

    def _check_ssh_connectivity(self, ip_address, username, pkey):
        ssh = remote_client.RemoteClient(ip_address, username, pkey=pkey)
        ssh.validate_authentication()
