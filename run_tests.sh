#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Gceapi's test suite(s)"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local environment"
  echo "  -f, --force              Force a clean re-build of the virtual environment. Useful when dependencies have been added."
  echo "  -u, --update             Update the virtual environment with any newer package versions"
  echo "  --unittests-only         Run unit tests only, exclude functional tests."
  echo "  -p, --flake8             Just run flake8"
  echo "  -P, --no-flake8          Don't run static code checks"
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "Note: with no options specified, the script will try to run the tests in a virtual environment,"
  echo "      If no virtualenv is found, the script will ask if you would like to create one.  If you "
  echo "      prefer to run tests NOT in a virtual environment, simply pass the -N option."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) let always_venv=1; let never_venv=0;;
    -N|--no-virtual-env) let always_venv=0; let never_venv=1;;
    -p|--flake8) let just_flake8=1;;
    -P|--no-flake8) let no_flake8=1;;
    -f|--force) let force=1;;
    -u|--update) update=1;;
    --unittests-only) noseopts="$noseopts --exclude-dir=gceapi/tests/functional";;
    -c|--coverage) noseopts="$noseopts --with-coverage --cover-package=gceapi";;
    -*) noseopts="$noseopts $1";;
    *) noseargs="$noseargs $1"
  esac
}

venv=.venv
with_venv=tools/with_venv.sh
always_venv=0
never_venv=0
force=0
noseopts=
noseargs=
wrapper=""
just_flake8=0
no_flake8=0
update=0

export NOSE_WITH_OPENSTACK=1
export NOSE_OPENSTACK_COLOR=1
export NOSE_OPENSTACK_RED=0.05
export NOSE_OPENSTACK_YELLOW=0.025
export NOSE_OPENSTACK_SHOW_ELAPSED=1
export NOSE_OPENSTACK_STDOUT=1

for arg in "$@"; do
  process_option $arg
done

function run_tests {
  # Cleanup *pyc
  ${wrapper} find . -type f -name "*.pyc" -delete
  # Just run the test suites in current environment
  ${wrapper} rm -f tests.sqlite
  ${wrapper} $NOSETESTS
}

function run_flake8 {
  echo "Running flake8 ..."
  if [ $never_venv -eq 1 ]; then
      echo "**WARNING**:" >&2
      echo "Running flake8 without virtual env may miss OpenStack HACKING detection" >&2
  fi

  ${wrapper} flake8
}


NOSETESTS="nosetests $noseopts $noseargs"

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ $update -eq 1 ]; then
    echo "Updating virtualenv..."
    python tools/install_venv.py
  fi
  if [ -e ${venv} ]; then
    wrapper="${with_venv}"
  else
    if [ $always_venv -eq 1 ]; then
      # Automatically install the virtualenv
      python tools/install_venv.py
      wrapper="${with_venv}"
    else
      echo -e "No virtual environment found...create one? (Y/n) \c"
      read use_ve
      if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        # Install the virtualenv and run the test suite in it
        python tools/install_venv.py
		    wrapper=${with_venv}
      fi
    fi
  fi
fi

if [ $just_flake8 -eq 1 ]; then
    run_flake8
    exit
fi

run_tests || exit

if [ -z "$noseargs" ]; then
    if [ $no_flake8 -eq 0 ]; then
        run_flake8
    fi
fi
