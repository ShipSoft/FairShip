#!/bin/bash
REPO="anaderi/ship-dev"
TAG="0.0.9"
BLD_DIR="build"

[ -d "$1" ] && BLD_DIR=$1
[ -n "$2" ] && TAG=$2

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

ADD . $path

EOF
docker build --rm -t $REPO:$TAG $path
echo "to check: docker run -ti --rm $REPO:$TAG sh"
