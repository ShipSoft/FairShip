#!/bin/bash
VM_TITLE="FairShip_proxy"
uuid=`VBoxManage list vms | grep "$VM_TITLE" | awk '{print $2}'| sed s/[{}]//g`
name=`VBoxManage list vms | grep "$VM_TITLE" | awk '{print $1}'`
[ -z "$uuid" ] && echo "Cannot find FairShip proxy VM ($VM_TITLE)" && exit
echo -n "Are you sure you want to delete '$name' machine [y/N] "
read answer
if [[ $answer = "y" || $answer = "Y" ]] ; then
  VBoxManage unregistervm $uuid --delete
fi