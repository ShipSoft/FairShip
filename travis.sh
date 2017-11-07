#!/bin/bash

set -e -x

echo ${TRAVIS_OS_NAME}
fairship=`pwd`

cd ..

# update and install packages
if [ "$TRAVIS_OS_NAME" = "osx" ]; then
   sw_vers
   osx_vers=`sw_vers -productVersion | cut -d . -f1 -f2`
   brew update >& /dev/null
   # oclint conflicts with gcc, gcc is needed for gfortran run-time
   brew cask uninstall oclint
   brew install gcc
   brew install cloc

   # get clang 3.9 for clang-format and clang-tidy
   wget http://releases.llvm.org/3.9.0/clang+llvm-3.9.0-x86_64-apple-darwin.tar.xz 2> /dev/null
   tar xf clang+llvm-3.9.0-x86_64-apple-darwin.tar.xz > /dev/null
   export LLVMDIR="`pwd`/clang+llvm-3.9.0-x86_64-apple-darwin"
   #export CC=$LLVMDIR/bin/clang
   #export CXX=$LLVMDIR/bin/clang++
   #export CXXFLAGS=-I$LLVMDIR/include
   #export LDFLAGS=-L$LLVMDIR/lib
   export DYLD_LIBRARY_PATH=$LLVMDIR/lib:$DYLD_LIBRARY_PATH
   export PATH=$LLVMDIR/bin:$PATH:

   export PKG_CONFIG_PATH=/usr/local/opt/openssl/lib/pkgconfig
   export PYTHON=/usr/bin/python
   export FAIRSOFTTAR="https://cernbox.cern.ch/index.php/s/LQbdnj9yDgfgBim/download"
   export FAIRROOTTAR="https://cernbox.cern.ch/index.php/s/YkR2hxqdk3s1T1j/download"
   export FAIRSOFT_VERSION=osx12-Jul13
   export FAIRROOT_VERSION=osx12-Jul13
fi

if [ "$TRAVIS_OS_NAME" = "linux" ]; then
   #sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test  # gcc-5
   #wget -O - http://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
   #sudo apt-add-repository -y "deb http://apt.llvm.org/trusty/ llvm-toolchain-trusty-3.9 main"
   #sudo apt-get update
   #sudo apt-get -y install gfortran
   #sudo apt-get -y install gcc-5 g++-5
   #sudo apt-get -y install valgrind
   #sudo apt-get -y install doxygen
   #sudo apt-get -y install cloc
   #sudo apt-get -y install clang-format-3.9 clang-tidy-3.9
   #export CC=gcc-5
   #export CXX=g++-5

   wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
   chmod +x miniconda.sh
   ./miniconda.sh -b
   export PATH=/home/travis/miniconda2/bin:$PATH
   conda update --yes conda
   conda install --yes python=2.7 numpy scipy
   conda install --yes libgfortran

   export PYTHON=python
   export FAIRSOFTTAR="https://cernbox.cern.ch/index.php/s/ciIustpVqDbLvxF/download"
   export FAIRROOTTAR="https://cernbox.cern.ch/index.php/s/XxwkA47XHruUGIA/download"
   export FAIRSOFT_VERSION=trusty-Jul13
   export FAIRROOT_VERSION=trusty-Jul13
fi

# install FairSoft
wget --progress=dot:giga --no-check-certificate $FAIRSOFTTAR -O FairSoft-${FAIRSOFT_VERSION}.tgz
tar zxf FairSoft-${FAIRSOFT_VERSION}.tgz

# install FairRoot
wget --progress=dot:giga --no-check-certificate $FAIRROOTTAR -O FairRoot-${FAIRSOFT_VERSION}.tgz
tar zxf FairRoot-${FAIRROOT_VERSION}.tgz

# output compiler information
echo ${CXX}
${CXX} --version
${CXX} -v

cd $fairship

# run following commands only on Linux
if [ "$TRAVIS_OS_NAME" = "osx" ]; then
   cloc .
fi

# add master branch
# https://github.com/travis-ci/travis-ci/issues/6069
git remote set-branches --add origin master

# build FairShip
./configure.sh || exit 1

# run FairShip tests
cd ../FairShipRun
. config.sh
$PYTHON ../FairShip/macro/run_simScript.py --test

# run following commands only on Linux
if [ "$TRAVIS_OS_NAME" = "osx" ]; then
   cd ../FairShip
   #make check-submission
fi
