gceapi_group = cfg.OptGroup(name='gceapi',
                            title='GCE options')
GCEAPIGroup = [
    cfg.StrOpt('catalog_type',
               default='gce',
               help="Catalog type of the GCE API service."),
    cfg.StrOpt('service_source',
               default=None,
               help="Hostname or IP-address to be used as a substitution "
                    "for the ones present in keystone service URLs to allow "
                    "tempest operations when services in keystone are "
                    "registered with local (inaccessible from the outside) "
                    "URLs. "
                    "Example: http://127.0.0.1:8080/v2.0/ is replaced with "
                    "https://www.com:443/v2.0/ when this parameter is "
                    "https://www.com:443"),
    cfg.StrOpt('api_path',
               default='/compute/v1/projects',
               help='GCE API path'),
    cfg.StrOpt('machine_type',
               default="m1.tiny",
               help='Instance flavor, '
               'leave empty for the default one (minimal RAM flavor)'),
    cfg.BoolOpt('skip_bootable_volume',
                default=False,
                help='Skip bootable volume tests'),
    cfg.BoolOpt('skip_empty_volume',
                default=False,
                help='Skip empty volume tests'),
    cfg.StrOpt('existing_image',
               default=None,
               help='Use existing if provided instead of loading one'),
    cfg.StrOpt('image_username',
               default='cirros',
               help="Username for http_raw_image"),
    cfg.StrOpt('http_raw_image',
               default='http://download.cirros-cloud.net/0.3.0/'
               'cirros-0.3.0-x86_64-disk.img',
               help="raw image url (http or file, tar or unpacked)"),
    cfg.IntOpt('operation_timeout',
               default=150,
               help='Time in seconds between image availability checks.'),
    cfg.IntOpt('operation_interval',
               default=5,
               help='Timeout in seconds to wait for an image to become'
                    'available.'),
    cfg.IntOpt('ping_timeout',
               default=150,
               help="Timeout in seconds to wait for ping to "
                    "succeed."),
    cfg.BoolOpt('use_floatingip',
                default=True,
                help="Should tests use Floating IP?"),
]
