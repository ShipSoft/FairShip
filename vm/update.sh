#!/bin/bash
IMAGE=anaderi/ocean:latest
VM_DIR=`dirname "$0"`
source $VM_DIR/_functions.sh

check_docker_connect

$DOCKER pull $IMAGE
