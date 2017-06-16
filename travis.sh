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
  brew install gcc
  brew install openssl
  export PKG_CONFIG_PATH=/usr/local/opt/openssl/lib/pkgconfig
  brew cask install xquartz
  brew install libtool
  export FAIRSOFT_VERSION=osx12-Jun16
fi

if [ "$TRAVIS_OS_NAME" = "linux" ]; then
  sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test  # gcc-5
  wget -O - http://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
  sudo apt-add-repository -y "deb http://apt.llvm.org/trusty/ llvm-toolchain-trusty-3.9 main"
  sudo apt-get update
  sudo apt-get -y install gcc-5 g++-5
  sudo apt-get -y install valgrind
  sudo apt-get -y install doxygen
  sudo apt-get -y install cloc
  sudo apt-get -y install clang-format-3.9 clang-tidy-3.9
  export CC=gcc-5
  export CXX=g++-5
  export FAIRSOFT_VERSION=trusty-Jun16
fi

# install FairSoft
#wget https://root.cern.ch/download/FairSoft-${FAIRSOFT_VERSION}.tgz 2> /dev/null
wget https://www.dropbox.com/s/4ya3s4o75kuz64f/FairSoft-osx12-Jun16.tgz 2> /dev/null

# install FairRoot
#wget https://root.cern.ch/download/FairRoot-${FAIRSOFT_VERSION}.tgz 2> /dev/null
wget https://www.dropbox.com/s/aafjbjcz6dyoidq/FairRoot-osx12-Jun16.tgz 2> /dev/null

# output compiler information
echo ${CXX}
${CXX} --version
${CXX} -v

cd $fairship

# run following commands only on Linux
if [ "$TRAVIS_OS_NAME" = "linux" ]; then
  cloc .
fi

# add master branch
# https://github.com/travis-ci/travis-ci/issues/6069
git remote set-branches --add origin master

# build FairShip
./configure.sh

# run FairShip tests
cd ../FairShipRun
. config.sh
python ../FairShip/macro/run_simScript.py --test

# run following commands only on Linux
if [ "$TRAVIS_OS_NAME" = "linux" ]; then
  cd ../FairShip
  make check-submission
fi
