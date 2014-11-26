#!/bin/bash

VERBOSE=0
DRYRUN=0
[[ $OSTYPE != darwin* ]] && echo "this script is for Mac only" && exit 1
[ "$1" = "-n" ] && DRYRUN=1

docker_ip() {
  boot2docker ip 2>/dev/null
}

ip=`docker_ip`
[ ! -n "$ip" ] && echo "unable to determine VM IP" && exit
DEST=`docker_ip`:5900

if [ $DRYRUN -eq 1 ] ; then
  echo "Connecting to: $DEST"
else
  open -a "VNC viewer" --args $DEST
fi
