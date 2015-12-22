# Copyright 2012 OpenStack Foundation
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


from oslo_config import cfg


OPTIONS_GROUP = cfg.OptGroup(name='gce', title='GCE options')
OPTIONS = [
    # Generic options
    cfg.IntOpt('build_timeout',
               default=180,
               help='Timeout for build resources'),
    cfg.IntOpt('build_interval',
               default=1,
               help='Interval between acquiring resource in wait func'),

    # GCE auth options
    cfg.StrOpt('cred_type',
               default='os_token',
               help='Method how to get credentials:'
                    '\n\tos_token - request token from OS keystone directly'
                    '\n\tgcloud_auth - use app credentials that should be'
                        'obtained before via gcloud auth'),
    cfg.StrOpt('username',
               default=None,
               help='User name for OpenStack identity'),
    cfg.StrOpt('password',
               default=None,
               help='User password for user in OpenStack'),
    cfg.StrOpt('auth_url',
               default='http://localhost:5000/v2.0/',
               help='Auth API relative URL in case of OpenStack identity'),

    # GCE API schema
    cfg.StrOpt('schema',
               default='etc/gceapi/protocols/v1.json',
               help='Json file with API schema for validation'),

    # GCE services address
    cfg.StrOpt('protocol',
               default='http',
               help='GCE protocl (http or https)'),
    cfg.StrOpt('host',
               default='localhost',
               help='GCE service host'),
    cfg.IntOpt('port',
               default=8787,
               help='GCE service port'),

    # GCE API URLs
    cfg.StrOpt('discovery_url',
               default='/discovery/v1/apis/{api}/{apiVersion}/rest',
               help='Discovery API relative URL'),

    # GCE resource IDs for testing
    # Note that Google's project has Name, ID and Number, for project
    # identification ID should be used, but in Openstack project has
    # Name and ID, where Name is corresponds to Project ID in Google, ID is
    # Openstack ID's and has no relation to Google's ID and Number.
    cfg.StrOpt('project_id',
               default=None,
               help='GCE Project ID for testing'),
    cfg.StrOpt('zone',
               default='nova',
               help='GCE Zone for testing'),
    cfg.StrOpt('region',
               default='regionone',
               help='GCE Region for testing'),
    cfg.StrOpt('networking',
               default='neutron',
               help='Types of OS networking: neutron or nova-network'),

    cfg.StrOpt('machine_type',
               default='n1-standard-1',
               help='Machine type - a type of instance ot be created'),
    cfg.StrOpt('image',
               default=None,
               help='Image to create instances. For example:'
               'debian-cloud/global/images/debian-7-wheezy-v20150929'),
]
