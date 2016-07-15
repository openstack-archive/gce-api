# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara
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

"""Generic Node base class for all workers that run on hosts."""

import signal
import sys

import eventlet
import greenlet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import eventlet_backdoor
from oslo_utils import importutils

from gceapi.i18n import _
from gceapi import wsgi

LOG = logging.getLogger(__name__)

service_opts = [
    cfg.BoolOpt('use_ssl',
                default=False,
                help='Enable ssl connections or not'),
    cfg.IntOpt('service_down_time',
               default=60,
               help='maximum time since last check-in for up service'),
    cfg.StrOpt('gceapi_listen',
               default="0.0.0.0",
               help='IP address for gce api to listen'),
    cfg.IntOpt('gceapi_listen_port',
               default=8787,
               help='port for gce api to listen'),
    ]

CONF = cfg.CONF
CONF.register_opts(service_opts)


class SignalExit(SystemExit):
    def __init__(self, signo, exccode=1):
        super(SignalExit, self).__init__(exccode)
        self.signo = signo


class Launcher(object):
    """Launch one or more services and wait for them to complete."""

    def __init__(self):
        """Initialize the service launcher.

        :returns: None

        """
        self._services = []
        self.backdoor_port = eventlet_backdoor.initialize_if_enabled(CONF)

    @staticmethod
    def run_server(server):
        """Start and wait for a server to finish.

        :param service: Server to run and wait for.
        :returns: None

        """
        server.start()
        server.wait()

    def launch_server(self, server):
        """Load and start the given server.

        :param server: The server you would like to start.
        :returns: None

        """
        if self.backdoor_port is not None:
            server.backdoor_port = self.backdoor_port
        gt = eventlet.spawn(self.run_server, server)
        self._services.append(gt)

    def stop(self):
        """Stop all services which are currently running.

        :returns: None

        """
        for service in self._services:
            service.kill()

    def wait(self):
        """Waits until all services have been stopped, and then returns.

        :returns: None

        """
        for service in self._services:
            try:
                service.wait()
            except greenlet.GreenletExit:
                pass


class ServiceLauncher(Launcher):
    def _handle_signal(self, signo, frame):
        # Allow the process to be killed again and die from natural causes
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        raise SignalExit(signo)

    def wait(self):
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        LOG.debug(_('Full set of CONF:'))
        for flag in CONF:
            flag_get = CONF.get(flag, None)
            # hide flag contents from log if contains a password
            if ("_password" in flag or "_key" in flag or
                    (flag == "sql_connection" and "mysql:" in flag_get)):
                LOG.debug(_('%(flag)s : FLAG SET ') % {'flag': flag})
            else:
                LOG.debug('%(flag)s : %(flag_get)s' % {'flag': flag,
                                                       'flag_get': flag_get})

        status = None
        try:
            super(ServiceLauncher, self).wait()
        except SignalExit as exc:
            signame = {signal.SIGTERM: 'SIGTERM',
                       signal.SIGINT: 'SIGINT'}[exc.signo]
            LOG.info(_('Caught %s, exiting'), signame)
            status = exc.code
        except SystemExit as exc:
            status = exc.code
        finally:
            self.stop()

        if status is not None:
            sys.exit(status)


class WSGIService(object):
    """Provides ability to launch API from a 'paste' configuration."""

    def __init__(self, name, loader=None, use_ssl=False, max_url_len=None):
        """Initialize, but do not start the WSGI server.

        :param name: The name of the WSGI server given to the loader.
        :param loader: Loads the WSGI application using the given name.
        :returns: None

        """
        self.name = name
        self.manager = self._get_manager()
        self.loader = loader or wsgi.Loader()
        self.app = self.loader.load_app(name)
        self.host = getattr(CONF, '%s_listen' % name, "0.0.0.0")
        self.port = getattr(CONF, '%s_listen_port' % name, 0)
        self.use_ssl = use_ssl
        self.server = wsgi.Server(name,
                                  self.app,
                                  host=self.host,
                                  port=self.port,
                                  use_ssl=self.use_ssl,
                                  max_url_len=max_url_len)
        # Pull back actual port used
        self.port = self.server.port
        self.backdoor_port = None

    def _get_manager(self):
        """Initialize a Manager object appropriate for this service.

        Use the service name to look up a Manager subclass from the
        configuration and initialize an instance. If no class name
        is configured, just return None.

        :returns: a Manager instance, or None.

        """
        fl = '%s_manager' % self.name
        if fl not in CONF:
            return None

        manager_class_name = CONF.get(fl, None)
        if not manager_class_name:
            return None

        manager_class = importutils.import_class(manager_class_name)
        return manager_class()

    def start(self):
        """Start serving this service using loaded configuration.

        Also, retrieve updated port number in case '0' was passed in, which
        indicates a random port should be used.

        :returns: None

        """
        if self.manager:
            self.manager.init_host()
            self.manager.pre_start_hook()
        if self.backdoor_port is not None:
            self.manager.backdoor_port = self.backdoor_port
        self.server.start()
        if self.manager:
            self.manager.post_start_hook()

    def stop(self):
        """Stop serving this API.

        :returns: None

        """
        self.server.stop()

    def wait(self):
        """Wait for the service to stop serving this API.

        :returns: None

        """
        self.server.wait()


# NOTE(vish): the global launcher is to maintain the existing
#             functionality of calling service.serve +
#             service.wait
_launcher = None


def serve(server):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = ServiceLauncher()
    _launcher.launch_server(server)


def wait():
    _launcher.wait()
