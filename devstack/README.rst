======================
 Enabling in Devstack
======================

1. Download DevStack

2. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin gce-api https://github.com/stackforge/gce-api

3. run ``stack.sh``
