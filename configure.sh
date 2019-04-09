#!/bin/bash
echo "*** You are using an old script which is not anymore supported."
echo "*** Please read the instructions at https://github.com/ShipSoft/FairShip"

exit 1
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
         echo "*** execute lcg setup with gcc62"
         /cvmfs/sft.cern.ch/lcg/releases/lcgenv/latest/lcgenv -p /cvmfs/sft.cern.ch/lcg/releases/LCG_87 x86_64-slc6-gcc62-opt Python >> tmp.sh
         source tmp.sh
         rm tmp.sh
      fi
   fi
fi

if [[ $HOSTNAME == *"cern.ch"* ]];
then
    echo "discovered lxplus: take gcc6.2 from lcg"
    source /cvmfs/sft.cern.ch/lcg/external/gcc/6.2/x86_64-slc6-gcc62-opt/setup.sh
    export GCCVERSION="x86_64-slc6-gcc62-opt"
    export LCGVERSION="LCG_87"
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
   cmake ../FairShip -DCMAKE_CXX_COMPILER=$xx -DCMAKE_C_COMPILER=$yy -DGCCVERSION="$GCCVERSION" -DLCGVERSION="$LCGVERSION" 
   make
fi
# fix a bug in FairRoot ?
sed -i 's|\. |source |g' ../FairShipRun/config.csh
sed -i 's|\. |source |g' ../FairShipRun/config.sh

