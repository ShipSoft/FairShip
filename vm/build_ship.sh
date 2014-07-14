#!/bin/bash

vrun=`dirname $0`/run.sh

BUILD_DIR="/opt/ship/build"

if [ "$1" = "-r" ] ; then
	$vrun "rm -rf $BUILD_DIR"
	shift
fi

$vrun "mkdir -p $BUILD_DIR; cd $BUILD_DIR; cmake ..; make"