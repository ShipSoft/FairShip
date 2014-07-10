#!/bin/bash
IMAGE=anaderi/ocean:latest
d=`which docker`

if [ -n "$d" ] ; then 
    $d ps > /dev/null 2>&1
    if [[ $? -ne 0 ]] ; then
	export DOCKER_HOST=tcp://:2375
	$d ps > /dev/null 2>&1
	if [[ $? -ne 0 ]] ; then
	    echo "cannot connect to docker. has it started? is DOCKER_HOST set?"
	    exit
	fi
	echo "Hint: export DOCKER_HOST=tcp://:2375"
    fi
    $d pull $IMAGE
else
    echo "At the moment this script works only with docker installed. Unless it is not the case,"
    echo "you can run 'ssh -p 2222 docker@localhost' pass: tcuser"
    echo "once there, you can run 'docker pull $IMAGE' which will bring latest image updates"
    echo "Otherwise you can recreate VM: vm/vdestroy.sh  ; vm/vstart.sh"
fi
