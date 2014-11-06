#!/bin/bash
IMAGE=anaderi/ocean:latest
which boot2docker > /dev/null
[ $? -ne 0 ] && echo "boot2docker is not found" && exit
`boot2docker shellinit`

docker pull $IMAGE
