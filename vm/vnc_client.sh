#!/bin/bash

[[ $OSTYPE != darwin* ]] && echo "this script is for Mac only" && exit 1

docker_ip() {
  boot2docker ip 2>/dev/null
}

ip=`docker_ip`
[ ! -n "$ip" ] && echo "unable to determine VM IP" && exit

open -a "VNC viewer" --args `docker_ip`:5900
