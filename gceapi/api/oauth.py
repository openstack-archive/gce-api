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

import base64
import json
import time
import uuid

from keystoneclient import client as keystone_client
from keystoneclient import exceptions
from oslo_config import cfg
from oslo_log import log as logging
import webob

from gceapi.i18n import _
from gceapi import wsgi_ext as openstack_wsgi

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


INTERNAL_GCUTIL_PROJECTS = ["debian-cloud", "centos-cloud", "suse-cloud",
                            "rhel-cloud", "windows-cloud", "google",
                            "coreos-cloud", "opensuse-cloud"]


class OAuthFault(openstack_wsgi.Fault):
    """Fault compliant with RFC

    To prevent extra info added by openstack.wsgi.Fault class
    to response which is not compliant RFC6749.
    """
    @webob.dec.wsgify(RequestClass=openstack_wsgi.Request)
    def __call__(self, req):
        return self.wrapped_exc


class Controller(object):
    """Simple OAuth2.0 Controller

    If you need other apps to work with GCE API you should add it here
    in VALID_CLIENTS.
    Based on https://developers.google.com/accounts/docs/OAuth2InstalledApp
    and on RFC 6749(paragraph 4.1).
    """

    AUTH_TIMEOUT = 300
    VALID_CLIENTS = {
        "32555940559.apps.googleusercontent.com": "ZmssLNjJy2998hD4CTg2ejr2",
        "1025389682001.apps.googleusercontent.com": "xslsVXhA7C8aOfSfb6edB6p6",
    }

    INTERNAL_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
    AUTH_PAGE_TEMPLATE =\
        "<!DOCTYPE html>"\
        "<html xmlns=\"http://www.w3.org/1999/xhtml\"><body>"\
        "Enter Openstack username and password to access GCE API<br/>"\
        "<br/>"\
        "<form action=\"approval\" name=\"approval\" method=\"post\">"\
        "<input type=\"hidden\" name=\"redirect_uri\" value=\""\
        + "{redirect_uri}\"/>"\
        "<input type=\"hidden\" name=\"code\" value=\"{code}\"/>"\
        "<input type=\"text\" name=\"username\" value=\"\"/><br/>"\
        "<input type=\"password\" name=\"password\" value=\"\"/><br/>"\
        "<input type=\"submit\" value=\"Login\"/>"\
        "</form>"\
        "</body></html>"

    class Client(object):
        auth_start_time = 0
        auth_token = None
        expires_in = 1

    # NOTE(apavlov): there is no cleaning of the dictionary
    _clients = {}

    def _check_redirect_uri(self, uri):
        if uri is None:
            msg = _("redirect_uri should be present")
            raise webob.exc.HTTPBadRequest(explanation=msg)
        if "localhost" not in uri and uri != self.INTERNAL_REDIRECT_URI:
            msg = _("redirect_uri has invalid format."
                    "it must confirms installed application uri of GCE")
            json_body = {"error": "invalid_request",
                         "error_description": msg}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))

    def auth(self, req):
        """OAuth protocol authorization endpoint handler

        Returns login authorization webpage invoked for example by gcutil auth.
        """
        client_id = req.GET.get("client_id")
        if client_id is None or client_id not in self.VALID_CLIENTS:
            json_body = {"error": "unauthorized_client"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))

        if req.GET.get("response_type") != "code":
            json_body = {"error": "unsupported_response_type"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))
        self._check_redirect_uri(req.GET.get("redirect_uri"))

        code = base64.urlsafe_b64encode(uuid.uuid4().bytes).replace('=', '')
        self._clients[code] = self.Client()
        self._clients[code].auth_start_time = time.time()

        html_page = self.AUTH_PAGE_TEMPLATE.format(
            redirect_uri=req.GET.get("redirect_uri"),
            code=code)
        return html_page

    def approval(self, req):
        """OAuth protocol authorization endpoint handler second part

        Returns webpage with verification code or redirects to provided
        redirect_uri specified in auth request.
        """
        code = req.POST.get("code")
        if code is None:
            json_body = {"error": "invalid_request"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))

        client = self._clients.get(code)
        if client is None:
            json_body = {"error": "invalid_client"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))

        if time.time() - client.auth_start_time > self.AUTH_TIMEOUT:
            raise webob.exc.HTTPRequestTimeout()

        redirect_uri = req.POST.get("redirect_uri")
        self._check_redirect_uri(redirect_uri)

        username = req.POST.get("username")
        password = req.POST.get("password")

        try:
            keystone = keystone_client.Client(
                username=username,
                password=password,
                auth_url=CONF.keystone_url)
            if keystone.auth_ref is None:
                # Ver2 doesn't create session and performs
                # authentication automatically, but Ver3 does create session
                # if it's not provided and doesn't perform authentication.
                # TODO(alexy-mr): use sessions
                keystone.authenticate()
            client.auth_token = keystone.auth_token
            s = keystone.auth_ref.issued
            e = keystone.auth_ref.expires
            client.expires_in = (e - s).seconds
        except Exception as ex:
            return webob.exc.HTTPUnauthorized(ex)

        if redirect_uri == self.INTERNAL_REDIRECT_URI:
            return "<html><body>Verification code is: "\
                + code + "</body></html>"

        uri = redirect_uri + "?code=" + code
        raise webob.exc.HTTPFound(location=uri)

    def token(self, req):
        """OAuth protocol authorization endpoint handler second part

        Returns json with tokens(access_token and optionally refresh_token).
        """
        client_id = req.POST.get("client_id")
        if client_id is None or client_id not in self.VALID_CLIENTS:
            json_body = {"error": "unauthorized_client"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))
        valid_secret = self.VALID_CLIENTS[client_id]
        client_secret = req.POST.get("client_secret")
        if client_secret is None or client_secret != valid_secret:
            json_body = {"error": "unauthorized_client"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))

        if req.POST.get("grant_type") != "authorization_code":
            json_body = {"error": "unsupported_grant_type"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))

        code = req.POST.get("code")
        client = self._clients.get(code)
        if client is None:
            json_body = {"error": "invalid_client"}
            raise OAuthFault(webob.exc.HTTPBadRequest(json_body=json_body))

        result = {"access_token": client.auth_token,
                  "expires_in": client.expires_in,
                  "token_type": "Bearer"}
        return json.dumps(result)


class AuthProtocol(object):
    """Filter for translating oauth token to keystone token."""
    def __init__(self, app):
        self.app = app
        self.auth_url = CONF.keystone_url

    def __call__(self, env, start_response):
        auth_token = env.get("HTTP_AUTHORIZATION")
        if auth_token is None:
            return self._reject_request(start_response)

        project = env["PATH_INFO"].split("/")[1]
        try:
            keystone = keystone_client.Client(
                token=auth_token.split()[1],
                tenant_name=project,
                force_new_token=True,
                auth_url=self.auth_url)
            if keystone.auth_ref is None:
                # Ver2 doesn't create session and performs
                # authentication automatically, but Ver3 does create session
                # if it's not provided and doesn't perform authentication.
                # TODO(alexey-mr): use sessions
                keystone.authenticate()
            scoped_token = keystone.auth_token
            env["HTTP_X_AUTH_TOKEN"] = scoped_token
            return self.app(env, start_response)
        except exceptions.Unauthorized:
            if project in INTERNAL_GCUTIL_PROJECTS:
                # NOTE(apavlov): return empty if no such projects(by gcutil)
                headers = [('Content-type', 'application/json;charset=UTF-8')]
                start_response('200 Ok', headers)
                return ["{}"]

            return self._reject_request(start_response)

    def _reject_request(self, start_response):
        headers = [('Content-type', 'application/json;charset=UTF-8')]
        start_response('401 Unauthorized', headers)
        json_body = {"error": "access_denied"}
        return [json.dumps(json_body)]


def filter_factory(global_conf, **local_conf):
    def auth_filter(app):
        return AuthProtocol(app)
    return auth_filter


def create_resource():
    return openstack_wsgi.Resource(Controller())
