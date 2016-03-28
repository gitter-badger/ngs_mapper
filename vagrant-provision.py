#!/usr/bin/env python

import platform
import subprocess
import os
import sys
from os.path import *
import shutil
from glob import glob
import tempfile

# Provisions pipeline into Ubuntu, CentOS or RedHat VM
# Will essentially do everything in the README.md for installation
# Then runs nosetests -v ngs_mapper at the end

class NotSuperUserError(Exception): pass

def get_distribution():
    return platform.linux_distribution()

def shell_cmd( cmdstr, requireroot=False ):
    # Ensure root
    if requireroot and os.getuid() != 0:
        raise NotSuperUserError("You need to be superuser to run {0}".format(
            cmdstr
        ))
    # Run command in shell
    return subprocess.check_call(
        cmdstr, shell=True
    )

def clone_pipeline( source, dst ):
    dst = expanduser(dst)
    source = expanduser(source)
    if not isdir(dst):
        cmd = 'git clone {0} {1}'.format(source,dst)
    else:
        cmd = 'd=$(pwd); cd {0} && git stash && git pull && cd $d'.format(
            dst
        )
    shell_cmd( cmd ) 
    os.chdir(dst)

def get_python_version():
    return sys.version_info[0:3]

def install_python( version='2.7.8', installprefix='$HOME' ):
    '''
    Install python and leave python tempdir behind
    '''
    # where to install
    prefix = expandvars(installprefix)
    # Where python will be located
    pythonexe = join(prefix,'bin','python')
    # Don't reinstall
    if exists(pythonexe):
        return pythonexe

    cmd = 'python setup.py install_python --prefix {0} --version {1}'.format(
        installprefix, version
    )
    shell_cmd( cmd )

    # Path to python executable
    return pythonexe

def create_virtualenv( venvpath='$HOME/.ngs_mapper', pythonprefix='$HOME' ):
    '''
    Unpack and install a virtualenv to venvpath
    '''
    # to cd back later
    cwd = os.getcwd()

    # Where to install path
    venvpath = expandvars(venvpath)

    # Download and unpack
    shell_cmd(
        'wget --no-check-certificate https://pypi.python.org/packages/source/v/' \
        'virtualenv/virtualenv-1.11.6.tar.gz -O- | tar xzf -'
    )

    # Create virtualenv
    pythonpath = expandvars('{0}/bin/python'.format(pythonprefix))
    shell_cmd(
        '{0} virtualenv-1.11.6/virtualenv.py' \
        ' --prompt="(ngs_mapper) " {1}'.format(pythonpath,venvpath)
    )

    # Activate virtualenv
    shell_cmd(
        '. {0}/bin/activate'.format(venvpath)
    )

    return venvpath

def run_setup( venvpath ):
    activatepath = join(venvpath,'bin','activate')
    shell_cmd(
        '. {0}; python setup.py install'.format(activatepath)
    )

def install_pipeline(python_prefix):
    clone_pipeline('/vagrant', '~/ngs_mapper')
    install_python(installprefix=python_prefix)
    venvpath = create_virtualenv(pythonprefix=python_prefix)
    run_setup( venvpath )

def parse_args(args=sys.argv[1:]):
    import argparse

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        '--install-system-packages',
        dest='install_system',
        default=False,
        action='store_true',
        help='Just installs system packages only'
    )

    group.add_argument(
        '--install-pipeline',
        dest='install_pipeline',
        default=True,
        action='store_true',
        help='Installs pipeline'
    )

    parser.add_argument(
        '--python-prefix',
        dest='python_prefix',
        default='/usr',
        help='Python prefix to use[Default: %(default)s]'
    )

    return parser.parse_args(args)

def main( args ):
    if args.install_system:
        shell_cmd('python setup.py install_system_packages',True)
    else:
        install_pipeline(args.python_prefix)

if __name__ == '__main__':
    main(parse_args())