#!/bin/bash
#
# bootstrapping of FairShip
# mainly to be used once after git clone
if [ "x$SIMPATH" == "x" ]; then
# check if FairSoftInst exists one level up
 if [ -d $PWD/../FairSoftInst ]; then
   export SIMPATH=$PWD/../FairSoftInst
 else
    echo "*** No FairSoft installation directory is defined."
    echo "*** Please set the environment variable SIMPATH to the Fairsoft installation directory."
    exit 1
 fi 
fi
if [ "x$FAIRROOTPATH" == "x" ]; then
# check if FairRootInst exists one level up
 if [ -d $PWD/../FairRootInst ]; then
   export FAIRROOTPATH=$PWD/../FairRootInst
 elif [ -d $SIMPATH/../FairRootInst ]; then
   export FAIRROOTPATH=$SIMPATH/../FairRootInst
 else
    echo "*** No FairRoot installation directory is defined."
    echo "*** Please set the environment variable FAIRROOTPATH to the FairRoot installation directory."
    exit 1
 fi 
fi

# if on lxplus
distribution=$(lsb_release -is)
version=$(lsb_release -rs | cut -f1 -d.)     

if [ "$distribution$version" = "ScientificCERNSLC6" ]; then
 # operating system of last century
 xx=$($SIMPATH/bin/fairsoft-config --cxx)
 if [[ "$xx" =~ "devtoolset" ]]; then
 # check that FairSoft is compiled with devtoolset
  source scl_source enable python27
  source scl_source enable devtoolset-3
 fi
fi

if [ ! -d ../FairShipRun ]; then
 mkdir ../FairShipRun
 cd ../FairShipRun
 if [ "$distribution$version" = "ScientificCERNSLC6" ]; then
  cmake ../FairShip  -DCMAKE_CXX_COMPILER=$xx
 else 
  cmake ../FairShip 
 fi
else
 cd FairShipRun
fi

make
source config.sh
