#!/bin/bash

# This gives us the current directory that this script is in
THIS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Grab the current directory the user is in
CWD=$(pwd)
# Ensure virtpath is set
virtpath=$1
if [ -z "${virtpath}" ]
then
    # Virtualenvironment path
    echo "No virtpath given so using ${THIS}/.miseqpipeline"
    virtpath=${THIS}/.miseqpipeline
fi
# Where to store our goodies
binpath=${virtpath}/bin
# Where are all the source files
deppath=${THIS}/dependencies
# Where to store manpages
manpath=${virtpath}/man1

function pyinstall() {
    dirpath=$1
    oldpath=$(pwd)
    cd $dirpath
    rm -rf build dist
    python setup.py install
    _RET=$?
    cd $oldpath
}

# If any command exits then trap it and print error and exit
trap 'echo "Error running $BASH_COMMAND"; rm -rf man1; exit;' ERR SIGINT SIGTERM

# Create the virtual environment where everything will install to
virtualenv ${virtpath}
# Activate
. ${virtpath}/bin/activate

# Make sure we are in the repository directory
cd ${THIS}

# Ensure zlib.h is in include path(I guess we won't assume redhat here and just do rpm -qa stuff)
if [ -z "$(find $(echo | cpp -x c++ -Wp,-v 2>&1 | grep -v 'ignoring' | grep -v '^#' | grep -v '^End' | xargs) -type f -name zlib.h)" ]
then
    echo "Please ensure that the zlib development package is installed. Probably yum install zlib-devel or apt-get install zlib-devel"
    exit 1
fi

# Compile samtools if the samtools binary doesn't exist
if [ ! -e ${binpath}/samtools ]
then
    #cd ${THIS}/htslib
    #make > htslib.make.log 2>&1
    cd ${deppath}/samtools
    make > samtools.make.log 2>&1
    ln -s $(pwd)/samtools ${binpath}/samtools
fi

# Compile bwa if the bwa binary doesn't exist
if [ ! -e ${binpath}/bwa ]
then
    cd ${deppath}/bwa
    make > bwa.make.log 2>&1
    ln -s $(pwd)/bwa ${binpath}/bwa
fi

# Some manpage setup
# First cleanse the manpath dir
rm -rf ${manpath}
mkdir ${manpath}
# Find all the actual manpages and link them into the man1 directory
find . -type f -name '*.1' | while read f
do
    # Manpages start with .TH
    head -1 "$f" | grep -q '^.TH'
    if [ $? -eq 0 ]
    then
        path_to="$(cd $(dirname "$f") && pwd)/$(basename "$f")"
        ln -s "$path_to" "${manpath}/$(basename "$f")"
    fi
done

# Install all python packages
package_list=( distribute PyVCF numpy biopython nose pyparsing tornado six python-dateutil pyBWA )
cd ${deppath}
for package in ${package_list[@]}
do
    pdir=$(echo ${package}*)
    echo "Installing ${pdir}"
    pyinstall ${pdir} > ${pdir}/${package}.install.log 2>&1
    if [ $_RET -ne 0 ]
    then
        echo "${package} failed to install. Please check ${pdir}/${package}.install.log for more details."
    fi
done

# Symlink all of our goodies into venv bin
find ${THIS} -maxdepth 1 -type f -perm /u=x,g=x,o=x | while read f
do
    echo "Installing $f to $binpath"
    ln -s ${f} ${binpath}/
done

echo "miseqpipeline is now installed"
