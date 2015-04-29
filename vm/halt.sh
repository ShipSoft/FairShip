#!/bin/bash

VM_DIR=`dirname "$0"`
source $VM_DIR/_common.sh
[ $SYSTEM == "Linux" ] && halt "No need to halt on Linux"

boot2docker halt
