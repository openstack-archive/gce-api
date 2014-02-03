#!/usr/bin/env python

"""Tool for checking if patch contains a regression test.

Pass in gerrit review number as parameter, tool will download branch and run
modified tests without bug fix.
"""

import string
import subprocess
import sys

gerrit_number = None

#TODO(jogo) use proper optParser
if len(sys.argv) == 2:
    gerrit_number = sys.argv[1]
else:
    gerrit_number = None
    print ("no gerrit review number specified, running on latest commit"
            "on current branch.")


def run(cmd, fail_ok=False):
    print "running: %s" % cmd
    try:
        rval = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        if not fail_ok:
            print "The command above terminated with an error."
            sys.exit(1)
        pass
    return rval


test_works = False

if gerrit_number:
    original_branch = run("git rev-parse --abbrev-ref HEAD")
    run("git review -d %s" % gerrit_number)

# run new tests with old code
run("git checkout HEAD^ nova")
run("git checkout HEAD nova/tests")

# identify which tests have changed
tests = run("git whatchanged --format=oneline -1 | grep \"nova/tests\" "
            "| cut -f2").split()
test_list = []
for test in tests:
    test_list.append(string.replace(test[0:-3], '/', '.'))

if test_list == []:
    test_works = False
    expect_failure = ""
else:
    # run new tests, expect them to fail
    expect_failure = run(("tox -epy27 %s 2>&1" % string.join(test_list)),
                         fail_ok=True)
    if "FAILED (id=" in expect_failure:
        test_works = True

# cleanup
run("git checkout HEAD nova")
if gerrit_number:
    new_branch = run("git status | head -1 | cut -d ' ' -f 4")
    run("git checkout %s" % original_branch)
    run("git branch -D %s" % new_branch)


if test_works:
    print expect_failure
    print ""
    print "*******************************"
    print "FOUND a regression test"
else:
    print expect_failure
    print ""
    print "*******************************"
    print "NO regression test"
    sys.exit(1)
