#!/bin/bash
DOCKER_USER=$USER
TAG="0.0.9"
BLD_DIR="build"
VMPATH=/opt/ship/FairShip/build

[ -n "$1" ] && TAG=$1 && shift
[ -n "$1" ] && DOCKER_USER=$1 && shift
[ -d "$1" ] && BLD_DIR=$1 && shift

REPO="$DOCKER_USER/ship-dev"

docker images | grep $REPO | grep $TAG -q
if [ $? -eq 0 ] ; then
  echo "ERR: name '$REPO:$TAG' is already taken"
  exit 1
fi

for d in geometry python macro muonShieldOptimization ; do
  echo "copy $d -> $BLD_DIR"
  [ -d $BLD_DIR/$d ] && rm -rf $BLD_DIR/$d
  cp -r $d $BLD_DIR
done

path=$(readlink -f $BLD_DIR)

cat > $path/Dockerfile << EOF
FROM busybox
MAINTAINER Andrey Ustyuzhanin andrey.ustyuzhanin@cern.ch

ADD . $VMPATH

EOF
docker build --rm -t $REPO:$TAG $path
echo "to check: docker run -ti --rm $REPO:$TAG sh"
