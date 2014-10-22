#!/bin/bash
export BASEDIR=$(echo $(cd $(dirname "$0")/.. && pwd -P))

if [ "$1" = "diag" ] ; then
	echo "=== DIAGNOSTIC ==="
	uname -a
	top -l 1 | head
	sw_vers -productVersion 
	which vagrant
	vagrant --version
	which docker
	docker --version
	cat /etc/resolv.conf
	df -h
	netstat -nr
	ifconfig -a
	nslookup cdn-registry-1.docker.io
	# traceroute -q 2 -m 25 cdn-registry-1.docker.io
	ping -c 3 cdn-registry-1.docker.io
	curl https://cdn-registry-1.docker.io/
	echo
	echo "=== END OF DIAGNOSTIC ==="
	cd $BASEDIR/diag
	vagrant up --provider=docker
else
	export VAGRANT_CWD=$BASEDIR
	export VAGRANT_DOTFILE_PATH=$BASEDIR
	vagrant up --provider=docker
	echo "hint: export DOCKER_HOST=tcp://:2375"
fi

