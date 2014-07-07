#!/bin/bash
CMD=$*
IMAGE=anaderi/ocean:latest
DNS_OPTS=
d=`which docker`

if [ "$1" = "-d" ] ; then
  DNS=`cat /etc/resolv.conf | grep nameserver|head -1 | awk '{print $2}'`
  DNS_OPTS="--dns $DNS"
  shift
  CMD=$*
fi

# docker run -ti --rm -w /opt/ship/build  -v /vagrant:/opt/ship bash -l -c '. config.sh; python macro/run_simScript.py'
VOLUME=
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
    # $d run -ti -v /vagrant:/opt/ship --rm $IMAGE bash -l -c "$CMD"
    $d run -ti -v /vagrant:/opt/ship -p 5900:5900 $DNS_OPTS --rm $IMAGE bash -l -c "$CMD"
else
    vagrant docker-run -t -- bash -l -c $CMD
fi
