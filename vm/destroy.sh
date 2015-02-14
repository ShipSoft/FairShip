#!/bin/bash

VM_DIR=`dirname "$0"`
source $VM_DIR/_functions.sh
[ $SYSTEM == "Linux" ] && halt "No need to destroy on Linux"

boot2docker delete
