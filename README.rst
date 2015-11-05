OpenStack Nova GCE API README
-----------------------------

Support of GCE-API for OpenStack.

Installation
=====

Make sure that python-pip package is installed.

Check and correct default options in the begining of 'install.sh' file.

Run "install.sh".

Check for other options in /etc/gceapi/gceapi.conf if needed.

Run it - "gce-api".

Usage
=====

Download gcloud from Google and install it.
https://developers.google.com/compute/docs/gcutil/

There are two ways for using it:

1. Run authorization command:
	python google-cloud-sdk/platform/gcutil/gcutil --authorization_uri_base=http://localhost:8787 auth
  and next any other commands:
	python google-cloud-sdk/platform/gcutil/gcutil --api_host=http://localhost:8787/ --authorization_uri_base=http://localhost:8787 --project demo listzones

2. You have to have Google account
  You can activate an already-authorized account with
	gcloud config set account <account>
  or authorize a new account with
	gcloud auth login
  Next you must authorize in Openstack by running authorization command:
	gcutil --authorization_uri_base=http://localhost:8787 auth
  and next you can run any other commands: 
	gcutil --api_host=http://localhost:8787/ --authorization_uri_base=http://localhost:8787 --project demo listzones

Make gcutil always use your GCE API endpoint using '--api_host' flag and your GCE API
authorization endpoint using '--authorization_uri_base' flag. Also you can store this
settings in "~/.gcutil.flags" file.
 
If it doesn't work by some reason check that your PYTHONPATH is exported and set correctly to something like
``/usr/lib/python2.7/dist-packages:/usr/local/lib/python2.7/dist-packages``.

Limitations
===========

* Names are unique in GCE and are used for identification. Names are not unique in Nova. IDs are used instead.
Solution: GCE-managed OpenStack installation should also maintain unique naming.

* GCE IDs are ulong (8 bytes). Openstack IDs can be different (int, string) but mostly they are GUID (16 bytes).
Solution: Since Openstack IDs are of different length and nature and because GCE API never uses ID as a parameter
now, 8-byte hashes are generated and returned for any ID to report.

* GCE allows per-user SSH key specification, but Nova supports only one key.
Solution: Nova GCE API just uses first key.

* Default Openstack flavors are available as machine types. GCE doesn't allow symbol '.' in machine type names,
  that's why GCE API plugin converts symbols '.' into '-' in 'get' requests (e.g. request of machine types converts
  the name 'm1.tiny' into m1-tiny) and vise versa in 'put/post/delete' requests (e.g. instance creation converts
  the name 'n1-standard-1' to 'n1.standard.1').

Authentication specifics
========================

GCE API uses OAuth2.0 for authentication. Simple sufficient implementation of this protocol
was added into GCE API service in nova because of its absence in keystone.
Current implementation allows operation with several OpenStack projects for
one authenticated user as Google allows. For this initial token returned during
authentication doesn't contain information about project required by keystone.
Instead another authentication happens with each request when incoming project
information is added to existing user info and new token is acquired in keystone.

Supported Features
==================

Standard Query Params (except for fields and prettyPrint) are not supported.

Supported resource types

* Addresses
* Disks
* Firewalls
* Images
* Instances
* MachineTypes
* Networks
* Projects
* Regions
* Zones

Unsupported resource types

* ForwardingRules
* HttpHealthChecks
* TargetPools

In the lists below:
"+" means supported
"-" unsupported

+Addresses

+aggregatedList  GET  /project/aggregated/addresses
+delete  DELETE  /project/regions/region/addresses/address
+get  GET  /project/regions/region/addresses/address
+insert  POST  /project/regions/region/addresses
+list  GET  /project/regions/region/addresses

+Disks

+aggregatedList  GET  /project/aggregated/disks
+createSnapshot  POST  /project/zones/zone/disks/disk/createSnapshot
+delete  DELETE  /project/zones/zone/disks/disk
+get  GET  /project/zones/zone/disks/disk
+insert  POST  /project/zones/zone/disks
+list  GET  /project/zones/zone/disks

+Firewalls

+delete  DELETE  /project/global/firewalls/firewall
+get  GET  /project/global/firewalls/firewall
+insert  POST  /project/global/firewalls
+list  GET  /project/global/firewalls
-patch  PATCH  /project/global/firewalls/firewall
-update  PUT  /project/global/firewalls/firewall

-ForwardingRules

-aggregatedList  GET  /project/aggregated/forwardingRules
-delete  DELETE  /project/regions/region/forwardingRules/forwardingRule
-get  GET  /project/regions/region/forwardingRules/forwardingRule
-insert  POST  /project/regions/region/forwardingRules
-list  GET  /project/regions/region/forwardingRules
-setTarget  POST  /project/regions/region/forwardingRules/forwardingRule/setTarget

+GlobalOperations

+aggregatedList  GET  /project/aggregated/operations
+delete  DELETE  /project/global/operations/operation
+get  GET  /project/global/operations/operation
+list  GET  /project/global/operations

-HttpHealthChecks

-delete  DELETE  /project/global/httpHealthChecks/httpHealthCheck
-get  GET  /project/global/httpHealthChecks/httpHealthCheck
-insert  POST  /project/global/httpHealthChecks
-list  GET  /project/global/httpHealthChecks
-patch  PATCH  /project/global/httpHealthChecks/httpHealthCheck
-update  PUT  /project/global/httpHealthChecks/httpHealthCheck

+Images

+delete  DELETE  /project/global/images/image
-deprecate  POST  /project/global/images/image/deprecate
+get  GET  /project/global/images/image
+insert  POST  /project/global/images
+list  GET  /project/global/images

+Instances

+addAccessConfig  POST  /project/zones/zone/instances/instance/addAccessConfig
+aggregatedList  GET  /project/aggregated/instances
+attachDisk  POST  /project/zones/zone/instances/instance/attachDisk
+delete  DELETE  /project/zones/zone/instances/instance
+deleteAccessConfig  POST /project/zones/zone/instances/instance/deleteAccessConfig
+detachDisk  POST  /project/zones/zone/instances/instance/detachDisk
+get  GET  /project/zones/zone/instances/instance
-getSerialPortOutput  GET  /project/zones/zone/instances/instance/serialPort
+insert  POST  /project/zones/zone/instances
+list  GET  /project/zones/zone/instances
+reset  POST  /project/zones/zone/instances/instance/reset
-setMetadata  POST  /project/zones/zone/instances/instance/setMetadata
-setTags  POST  /project/zones/zone/instances/instance/setTags
-setScheduling  POST  /project/zones/zone/instances/instance/setScheduling

+MachineTypes

+aggregatedList  GET  /project/aggregated/machineTypes
+get  GET  /project/zones/zone/machineTypes/machineType
+list  GET  /project/zones/zone/machineTypes

+Networks

+delete  DELETE  /project/global/networks/network
+get  GET  /project/global/networks/network
+insert  POST  /project/global/networks
+list  GET  /project/global/networks

+Projects

+get  GET  /project
+setCommonInstanceMetadata  POST  /project/setCommonInstanceMetadata

-RegionOperations

+delete  DELETE  /project/regions/region/operations/operation
+get  GET  /project/regions/region/operations/operation
+list  GET  /project/regions/region/operations

+Regions

+get  GET  /project/regions/region
+list  GET  /project/regions

+Routes

+delete  DELETE  /project/global/routes/route
+get  GET  /project/global/routes/route
+insert  POST  /project/global/routes
+list  GET  /project/global/routes

+Snapshots

+delete  DELETE  /project/global/snapshots/snapshot
+get  GET  /project/global/snapshots/snapshot
+list  GET  /project/global/snapshots

-TargetPools

-addHealthCheck  POST /project/regions/region/targetPools/targetPool/addHealthCheck
-addInstance  POST  /project/regions/region/targetPools/targetPool/addInstance
-aggregatedList  GET  /project/aggregated/targetPools
-delete  DELETE  /project/regions/region/targetPools/targetPool
-get  GET  /project/regions/region/targetPools/targetPool
-getHealth  POST  /project/regions/region/targetPools/targetPool/getHealth
-insert  POST  /project/regions/region/targetPools
-list  GET  /project/regions/region/targetPools
-removeHealthCheck  POST /project/regions/region/targetPools/targetPool/removeHealthCheck
-removeInstance  POST /project/regions/region/targetPools/targetPool/removeInstance
-setBackup  POST  /project/regions/region/targetPools/targetPool/setBackup

+ZoneOperations

+delete  DELETE  /project/zones/zone/operations/operation
+get  GET  /project/zones/zone/operations/operation
+list  GET  /project/zones/zone/operations

+Zones

+get  GET  /project/zones/zone
+list  GET  /project/zones

