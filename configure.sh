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

if `which lsb_release > /dev/null 2>&1` ; then
   # if on lxplus
   distribution=$(lsb_release -is)
   version=$(lsb_release -rs | cut -f1 -d.)

   if [ "$distribution$version" = "ScientificCERNSLC6" ]; then
      # operating system of last century
      xx=$($SIMPATH/bin/fairsoft-config --cxx)
      if [[ "$xx" =~ "lcg" ]]; then
         # check that FairSoft is compiled with devtoolset
         if test "${SIMPATH#*gcc62}" != "$SIMPATH" ; then
            echo "*** execute lcg setup with gcc62"
            /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -p /afs/cern.ch/sw/lcg/releases/LCG_87 x86_64-slc6-gcc62-opt Python >> tmp.sh
         else
            echo "*** execute lcg setup with gcc49"
            /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -p /afs/cern.ch/sw/lcg/releases/LCG_85 x86_64-slc6-gcc49-opt Python >> tmp.sh
         fi
         source tmp.sh
         rm tmp.sh
      fi
   fi
fi

if [ ! -d ../FairShipRun ]; then
   mkdir ../FairShipRun
fi
cd ../FairShipRun

xx=$($SIMPATH/bin/fairsoft-config --cxx)
yy=$($SIMPATH/bin/fairsoft-config --cc)

if `which ninja > /dev/null 2>&1` ; then
   cmake -GNinja ../FairShip -DCMAKE_CXX_COMPILER=$xx -DCMAKE_C_COMPILER=$yy
   ninja
else
   cmake ../FairShip -DCMAKE_CXX_COMPILER=$xx -DCMAKE_C_COMPILER=$yy
   make
fi

source config.sh
