#!/usr/bin/python
"""
Install packages into chroot

Arguments:
  <packages> := ( - | path/to/plan | path/to/spec | package[=version] ) ...
                If a version isn't specified, the newest version is implied.

Options:
  -p --pool=PATH                Set pool path (default: $FAB_POOL_PATH)
  -a --arch=ARCH                Set architecture (default: $FAB_ARCH)
  -n --no-deps                  Do not resolve and install package dependencies
  -i --ignore-errors=PKG[: ...] Ignore errors generated by list of packages
  -e --env=VARNAME[: ...]       List of environment variable names to pass through
                                default: $FAB_INSTALL_ENV

  (Also accepts fab-cpp options to effect plan preprocessing)

Environment:

   FAB_SHARE_PATH               Path to directory containing initctl.dummy
                                default: /usr/share/fab
"""

import re
import os
from os.path import *

import sys
import getopt

import help
import cpp
from plan import Plan
from installer import Installer
from common import fatal, gnu_getopt

from cmd_chroot import get_environ

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <chroot> <packages>" % sys.argv[0]

def main():
    cpp_opts, args = cpp.getopt(sys.argv[1:])
    try:
        opts, args = gnu_getopt(args, 'np:a:i:e:',
                     ['pool=', 'arch=', 'ignore-errors=', 'env=', 'no-deps'])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    if not len(args) > 1:
        usage("bad number of arguments")

    pool_path = None
    arch = None
    opt_no_deps = False
    ignore_errors = []

    env_conf = os.environ.get('FAB_INSTALL_ENV')

    for opt, val in opts:
        if opt in ('-p', '--pool'):
            pool_path = val

        elif opt in ('-a', '--arch'):
            arch = val

        elif opt in ('-n', '--no-deps'):
            opt_no_deps = True

        elif opt in ('-i', '--ignore-errors'):
            ignore_errors = val.split(":")

        elif opt in ('-e', '--env'):
            env_conf = val

    chroot_path = args[0]
    if not os.path.isdir(chroot_path):
        fatal("chroot does not exist: " + chroot_path)

    if pool_path is None:
        pool_path = os.environ.get('FAB_POOL_PATH')

    if arch is None:
        arch = os.environ.get('FAB_ARCH')

    plan = Plan(pool_path=pool_path)
    for arg in args[1:]:
        if arg == "-" or exists(arg):
            plan |= Plan.init_from_file(arg, cpp_opts, pool_path)
        else:
            plan.add(arg)

    if not opt_no_deps:
        packages = list(plan.resolve())
    else:
        packages = list(plan)
        
    installer = Installer(chroot_path, pool_path, arch, get_environ(env_conf))
    installer.install(packages, ignore_errors)

if __name__=="__main__":
    main()

