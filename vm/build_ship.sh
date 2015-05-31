#!/bin/bash

vrun=`dirname $0`/run.sh
function num_proc() {
  N=1
  if [ `uname -s` == "Linux" ] ; then
    N=`cat /proc/cpuinfo |grep 'processor\s*:\s*\d*'|wc -l`
  elif [ `uname -s` == "Darwin" ] ; then
    N=`sysctl -n hw.ncpu`
  fi
  if [ `which bc &> /dev/null` ] ; then
    logN=`echo "l($N)" | bc -l`
    echo $logN/1+1| bc
  else
    result=$(( $N/2 ))
    [ $result -ge 8 ] && result=8
    echo $result
  fi
}

BUILD_DIR="/opt/ship/FairShip/build"
NP=`num_proc`

if [ "$1" = "-r" ] ; then
	$vrun "rm -rf $BUILD_DIR"
	shift
fi

echo $vrun "mkdir -p $BUILD_DIR; cd $BUILD_DIR; cmake -j $NP ..; make -j $NP"
