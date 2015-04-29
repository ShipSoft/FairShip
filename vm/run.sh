#!/bin/bash
DNS_OPTS=
CMD="bash"
VM_DIR=`dirname "$0"`
source $VM_DIR/_common.sh

check_docker_connect

if [ "$1" = "-d" ] ; then
  DNS=`cat /etc/resolv.conf | grep nameserver|head -1 | awk '{print $2}'`
  DNS_OPTS="--dns $DNS"
  shift
fi

LOCAL_SHIP=/vagrant
[ ! -d $LOCAL_SHIP ] && LOCAL_SHIP=`cd "${VM_DIR}/.." && pwd -P`
[ -n "$*" ] && CMD="$*"
$DOCKER run -ti -v $LOCAL_SHIP:/opt/ship/FairShip -p 5900:5900 $DNS_OPTS -w /opt/ship/FairShip --rm $IMAGE "$CMD"
