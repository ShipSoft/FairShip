#!/bin/bash

if [[ $HOSTNAME == *lxplus* ]]
then
  echo "Setup lcg environment"
  source FairShip/genenv.sh
# fixing a strange error in ROOT v6-10-06
  cp FairShip/map . 
  export PATH=$(pwd):${PATH}
fi

if [ ! -d alibuild ];
then
  git clone https://github.com/alisw/alibuild
fi

if [ ! -d shipdist ];
then
  git clone https://github.com/ShipSoft/shipdist
fi

if [ $# -eq 0 ]
  then

 alibuild/aliBuild -c shipdist/ --defaults fairship build FairShip

# not done by the framework
 if [ -f config.sh ];
 then
  rm config.sh
 fi

 alibuild/alienv printenv  FairShip/latest >> config.sh
 chmod u+x config.sh
 source config.sh
 cp $GENIE/data/evgen/pdfs/GRV98lo_patched.LHgrid $LHAPDF5_ROOT/share/lhapdf

else
  alibuild/aliDoctor -c shipdist/ --defaults fairship FairShip
fi
# assume everything is build and placed on cvmfs. How to get the correct environment, if not build there?
# alibuild/alienv printenv  FairShip/latest > config.sh
# source config.sh          # makes FairShip environment
# source FairShip/genenv.sh # makes lxplus environment, needs to be executed after config.sh
