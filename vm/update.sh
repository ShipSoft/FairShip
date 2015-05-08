#!/bin/bash
VM_DIR=`dirname "$0"`
source $VM_DIR/_common.sh

check_docker_connect

$DOCKER pull $IMAGE
