#!/bin/bash

SYSTEM=`uname -s`

halt() {
  echo $*
  exit 1
}

function check_docker_exec() {
  DOCKER=`which docker 2>&1` || halt "Cannot find docker client" 
}

function check_docker_connect() {
  [ -n "$DOCKER" ] || check_docker_exec 
  $DOCKER ps > /dev/null 2>&1 || halt "Cannot connect to docker. Is it started? is DOCKER_HOST set? use sudo?"
}
