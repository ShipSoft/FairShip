#!/bin/bash
IMAGE=anaderi/ocean:latest
DNS_OPTS=
dclient=`dirname $0`/docker
export DOCKER_HOST=tcp://:2375

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

$dclient ps > /dev/null 2>&1 || halt "cannot connect to docker. is it started?"
$dclient run -ti -v /vagrant:/opt/ship -p 5900:5900 $DNS_OPTS -w /opt/ship --rm $IMAGE "$*"
