# lib/gce-api

# Dependencies:
# ``functions`` file
# ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined

# ``stack.sh`` calls the entry points in this order:
#
# install_gceapi
# configure_gceapi
# start_gceapi
# stop_gceapi


# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace


# Defaults
# --------

# Set up default directories
GCEAPI_DIR=$DEST/gce-api
GCEAPI_CONF_DIR=${GCEAPI_CONF_DIR:-/etc/gceapi}
GCEAPI_CONF_FILE=${GCEAPI_CONF_DIR}/gceapi.conf
GCEAPI_DEBUG=${GCEAPI_DEBUG:-True}
GCEAPI_STATE_PATH=${GCEAPI_STATE_PATH:=$DATA_DIR/gceapi}

GCEAPI_SERVICE_PORT=${GCEAPI_SERVICE_PORT:-8787}

GCEAPI_RABBIT_VHOST=${GCEAPI_RABBIT_VHOST:-''}

GCEAPI_ADMIN_USER=${GCEAPI_ADMIN_USER:-gceapi}

GCEAPI_KEYSTONE_SIGNING_DIR=${GCEAPI_KEYSTONE_SIGNING_DIR:-/tmp/keystone-signing-gceapi}

# Support entry points installation of console scripts
if [[ -d $GCEAPI_DIR/bin ]]; then
    GCEAPI_BIN_DIR=$GCEAPI_DIR/bin
else
    GCEAPI_BIN_DIR=$(get_python_exec_prefix)
fi


function recreate_endpoint {
    local endpoint=$1
    local description=$2
    local port=$3

    # Remove nova's gce service/endpoint
    local endpoint_id=$(openstack endpoint list \
        --column "ID" \
        --column "Region" \
        --column "Service Name" \
        | grep " $REGION_NAME " \
        | grep " $endpoint " | get_field 1)
    if [[ -n "$endpoint_id" ]]; then
        openstack endpoint delete $endpoint_id
    fi
    local service_id=$(openstack service list \
        -c "ID" -c "Name" \
        | grep " $endpoint " | get_field 1)
    if [[ -n "$service_id" ]]; then
        openstack service delete $service_id
    fi

    local service_id=$(openstack service create \
        $endpoint \
        --name "$endpoint" \
        --description="$description" \
        -f value -c id)
    openstack --os-identity-api-version 3 endpoint create --region "$REGION_NAME" \
        $service_id public "$SERVICE_PROTOCOL://$SERVICE_HOST:$port/"
    openstack --os-identity-api-version 3 endpoint create --region "$REGION_NAME" \
        $service_id admin "$SERVICE_PROTOCOL://$SERVICE_HOST:$port/"
    openstack --os-identity-api-version 3 endpoint create --region "$REGION_NAME" \
        $service_id internal "$SERVICE_PROTOCOL://$SERVICE_HOST:$port/"
}


# create_gceapi_accounts() - Set up common required gceapi accounts
#
# Tenant      User       Roles
# ------------------------------
# service     gceapi     admin
function create_gceapi_accounts() {
    if ! is_service_enabled key; then
        return
    fi

    SERVICE_TENANT=$(openstack project list | awk "/ $SERVICE_TENANT_NAME / { print \$2 }")
    ADMIN_ROLE=$(openstack role list | awk "/ admin / { print \$2 }")

    GCEAPI_USER=$(openstack user create \
        $GCEAPI_ADMIN_USER \
        --password "$SERVICE_PASSWORD" \
        --project $SERVICE_TENANT \
        --email gceapi@example.com \
        | grep " id " | get_field 2)

    openstack role add \
        $ADMIN_ROLE \
        --project $SERVICE_TENANT \
        --user $GCEAPI_USER

    recreate_endpoint "gce" "GCE Compatibility Layer" $GCEAPI_SERVICE_PORT
}


function mkdir_chown_stack {
    if [[ ! -d "$1" ]]; then
        sudo mkdir -p "$1"
    fi
    sudo chown $STACK_USER "$1"
}


function configure_gceapi_rpc_backend() {
    # Configure the rpc service.
    iniset_rpc_backend gceapi $GCEAPI_CONF_FILE DEFAULT

    # TODO(ruhe): get rid of this ugly workaround.
    inicomment $GCEAPI_CONF_FILE DEFAULT rpc_backend

    # Set non-default rabbit virtual host if required.
    if [[ -n "$GCEAPI_RABBIT_VHOST" ]]; then
        iniset $GCEAPI_CONF_FILE DEFAULT rabbit_virtual_host $GCEAPI_RABBIT_VHOST
    fi
}

function configure_gceapi_networking {
    # Use keyword 'public' if gceapi external network was not set.
    # If it was set but the network is not exist then
    # first available external network will be selected.
    local ext_net=${GCEAPI_EXTERNAL_NETWORK:-'public'}
    # Configure networking options for gceapi
    if [[ -n "$ext_net" ]]; then
        iniset $GCEAPI_CONF_FILE DEFAULT public_network $ext_net
    fi

    if [[ ,${ENABLED_SERVICES} =~ ,"q-" ]]; then
        iniset $GCEAPI_CONF_FILE DEFAULT network_api quantum
    else
        iniset $GCEAPI_CONF_FILE DEFAULT network_api nova
    fi
}

# Entry points
# ------------

# configure_gceapi() - Set config files, create data dirs, etc
function configure_gceapi {
    mkdir_chown_stack "$GCEAPI_CONF_DIR"

    # Generate gceapi configuration file and configure common parameters.
    touch $GCEAPI_CONF_FILE
    cp $GCEAPI_DIR/etc/gceapi/api-paste.ini $GCEAPI_CONF_DIR

    cleanup_gceapi

    iniset $GCEAPI_CONF_FILE DEFAULT debug $GCEAPI_DEBUG
    iniset $GCEAPI_CONF_FILE DEFAULT use_syslog $SYSLOG
    iniset $GCEAPI_CONF_FILE DEFAULT state_path $GCEAPI_STATE_PATH


    # gceapi Api Configuration
    #-------------------------

    iniset $GCEAPI_CONF_FILE DEFAULT region $REGION_NAME
    iniset $GCEAPI_CONF_FILE DEFAULT keystone_url "$OS_AUTH_URL"

    # set default new empty disk size to 1GB, default production is 500
    # that corresponds to default Google pd-standard disk-type
    iniset $GCEAPI_CONF_FILE DEFAULT default_volume_size_gb 1

    iniset $GCEAPI_CONF_FILE keystone_authtoken admin_tenant_name $SERVICE_TENANT_NAME
    iniset $GCEAPI_CONF_FILE keystone_authtoken admin_user $GCEAPI_ADMIN_USER
    iniset $GCEAPI_CONF_FILE keystone_authtoken admin_password $SERVICE_PASSWORD
    iniset $GCEAPI_CONF_FILE keystone_authtoken identity_uri "$OS_AUTH_URL"

    configure_gceapi_rpc_backend

    # configure the database.
    iniset $GCEAPI_CONF_FILE database connection `database_connection_url gceapi`

    configure_gceapi_networking
}


# init_gceapi() - Initialize databases, etc.
function init_gceapi() {
    # (re)create gceapi database
    recreate_database gceapi utf8

    $GCEAPI_BIN_DIR/gce-api-manage --config-file $GCEAPI_CONF_FILE db_sync
}


# install_gceapi() - Collect source and prepare
function install_gceapi() {
    # TODO(ruhe): use setup_develop once gceapi requirements match with global-requirement.txt
    # both functions (setup_develop and setup_package) are defined at:
    # http://git.openstack.org/cgit/openstack-dev/devstack/tree/functions-common
    setup_package $GCEAPI_DIR -e
}


# start_gceapi() - Start running processes, including screen
function start_gceapi() {
    run_process gce-api "$GCEAPI_BIN_DIR/gce-api --config-file $GCEAPI_CONF_DIR/gceapi.conf"

    echo "Waiting for GCE API to start..."
    if ! wait_for_service $SERVICE_TIMEOUT \
                "$SERVICE_PROTOCOL://$SERVICE_HOST:$GCEAPI_SERVICE_PORT/"; then
        die $LINENO "GCE API did not start"
    fi
}


# stop_gceapi() - Stop running processes
function stop_gceapi() {
    # Kill the gceapi screen windows
    stop_process gce-api
}

function cleanup_gceapi() {

    # Cleanup keystone signing dir
    sudo rm -rf $GCEAPI_KEYSTONE_SIGNING_DIR
}

function configure_functional_tests() {
    (source $GCEAPI_DIR/devstack/create_config "functional_tests.conf")
    if [[ "$?" -ne "0" ]]; then
        warn $LINENO "GCE API tests config could not be created."
    elif is_service_enabled tempest; then
        cat "$GCEAPI_DIR/functional_tests.conf" >> $TEMPEST_CONFIG
    fi
}

# main dispatcher
if [[ "$1" == "stack" && "$2" == "install" ]]; then
    echo_summary "Installing gce-api"
    install_gceapi
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    echo_summary "Configuring gce-api"
    configure_gceapi
    create_gceapi_accounts
elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
    echo_summary "Initializing gce-api"
    init_gceapi
    start_gceapi
    configure_functional_tests
fi

if [[ "$1" == "unstack" ]]; then
    stop_gceapi
    cleanup_gceapi
fi

# Restore xtrace
$XTRACE

# Local variables:
# mode: shell-script
# End:
