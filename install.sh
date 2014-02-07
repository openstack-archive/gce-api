#!/bin/bash -e

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" >&2
    exit 1
fi

LOG_DIR=/var/log/gceapi
CONF_DIR=/etc/gceapi
CONF_FILE=$CONF_DIR/gceapi.conf
APIPASTE_FILE=$CONF_DIR/api-paste.ini
AUTH_CACHE_DIR=${AUTH_CACHE_DIR:-/var/cache/gceapi}
LOGGING_FORMAT="%(asctime)s.%(msecs)03d %(levelname)s %(name)s [%(request_id)s %(user_name)s %(project_name)s] %(instance)s%(message)s"
LOG_VERBOSE=True
CONNECTION="mysql://root:password@127.0.0.1/gceapi?charset=utf8"
SIGNING_DIR=/var/cache/gceapi
AUTH_HOST=127.0.0.1


# Determinate is the given option present in the INI file
# ini_has_option config-file section option
function ini_has_option() {
    local file=$1
    local section=$2
    local option=$3
    local line
    line=$(sed -ne "/^\[$section\]/,/^\[.*\]/ { /^$option[ \t]*=/ p; }" "$file")
    [ -n "$line" ]
}

# Set an option in an INI file
# iniset config-file section option value
function iniset() {
    local file=$1
    local section=$2
    local option=$3
    local value=$4
    if ! grep -q "^\[$section\]" "$file"; then
        # Add section at the end
        echo -e "\n[$section]" >>"$file"
    fi
    if ! ini_has_option "$file" "$section" "$option"; then
        # Add it
        sed -i -e "/^\[$section\]/ a\\
$option = $value
" "$file"
    else
        # Replace it
        sed -i -e "/^\[$section\]/,/^\[.*\]/ s|^\($option[ \t]*=[ \t]*\).*$|\1$value|" "$file"
    fi
}


#create log dir
echo Creating log dir
install -d $LOG_DIR

#copy conf files (do not override it)
echo Creating configs
mkdir -p /etc/gceapi > /dev/null
if [ ! -s $CONF_FILE ]; then
    cp etc/gceapi/gceapi.conf $CONF_FILE
fi
if [ ! -s $APIPASTE_FILE ]; then
    cp etc/gceapi/api-paste.ini $APIPASTE_FILE
fi
#update default config with some values
iniset $CONF_FILE DEFAULT api_paste_config $APIPASTE_FILE
iniset $CONF_FILE DEFAULT logging_context_format_string "$LOGGING_FORMAT"
iniset $CONF_FILE DEFAULT verbose $LOG_VERBOSE
iniset $CONF_FILE database connection "$CONNECTION"
iniset $CONF_FILE keystone_authtoken signing_dir $SIGNING_DIR
iniset $CONF_FILE keystone_authtoken auth_host $AUTH_HOST

#init cache dir
echo Creating signing dir
mkdir -p $AUTH_CACHE_DIR
chown $SUDO_USER $AUTH_CACHE_DIR
rm -f $AUTH_CACHE_DIR/*

#recreate database
echo Setuping database
bin/gceapi-db-setup deb

#install it
echo Installing package
python setup.py install
rm -rf build gce_api.egg-info
