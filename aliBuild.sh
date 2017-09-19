#!/bin/bash

# git clone https://github.com/PMunkes/FairShip
# source FairShip/aliBuild.sh

if [[ $HOSTNAME == *lxplus* ]]
then
  echo "Setup lcg environment"
  source FairShip/genenv.sh
fi

if [ ! -d alibuild ];
then
  git clone https://github.com/alisw/alibuild
fi

if [ ! -d shipdist ];
then
  git clone https://github.com/PMunkes/shipdist
fi

if [ ! -d OpenSSL ];
then
  git clone https://github.com/PMunkes/FairShip-openssl OpenSSL
fi

if [ ! -d FairRoot ];
then
 git clone https://github.com/PMunkes/FairRoot
 cd FairRoot
 git checkout fairshipdev
 cd ..
fi

alibuild/aliBuild -c shipdist/ --defaults fairship build FairShip

# not done by the framework
cp sw/SOURCES/GENIE/fairshipdev/fairshipdev/data/evgen/pdfs/GRV98lo_patched.LHgrid $LHAPDF5_ROOT/share/lhapdf

# assume everything is build and placed on cvmfs. How to get the correct environment, if not build there?
# alibuild/alienv printenv  FairShip/latest > config.sh
# source config.sh          # makes FairShip environment
# source FairShip/genenv.sh # makes lxplus environment, needs to be executed after config.sh
