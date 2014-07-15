#!/bin/bash
IMAGE=anaderi/ocean:latest
DNS_OPTS=
sys_dclient=`which docker 2>&1` 
if [ $? -eq 0 ] ; then 
  dclient=$sys_dclient
else
  dclient=`dirname $0`/docker
fi

if [ -z "$DOCKER_HOST" ] ; then
  export DOCKER_HOST=tcp://:2375
fi

halt() {
  echo $*
  exit 1
}

[ -z "$dclient" ] && echo "no docker client found" && exit 1

if [ "$1" = "-d" ] ; then
  DNS=`cat /etc/resolv.conf | grep nameserver|head -1 | awk '{print $2}'`
  DNS_OPTS="--dns $DNS"
  shift
fi

LOCAL_SHIP=/vagrant
[ -d $LOCAL_SHIP ] && LOCAL_SHIP=$( readlink -f `dirname $0`/".." )

$dclient ps > /dev/null 2>&1 || halt "cannot connect to docker. is it running?"
$dclient run -ti -v $LOCAL_SHIP:/opt/ship -p 5900:5900 $DNS_OPTS -w /opt/ship --rm $IMAGE "$*"
