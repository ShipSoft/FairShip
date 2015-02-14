#!/bin/bash

VM_DIR=`dirname "$0"`
source $VM_DIR/_functions.sh
[ $SYSTEM == "Linux" ] && halt "No need to destroy on Linux"

VM_TITLE="FairShip_"
name=`VBoxManage list vms | grep $VM_TITLE | awk '{print $1}' | sed 's/"//g'| head -1`
[ -z "$name" ] && echo "Cannot find FairShip proxy VM ($VM_TITLE)" && exit
echo -n "Are you sure you want to delete '$name' machine [y/N] "
read answer
if [[ $answer = "y" || $answer = "Y" ]] ; then
  VBoxManage unregistervm $name --delete
fi
