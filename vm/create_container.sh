#!/bin/bash
DOCKER_USER=$USER
TAG="0.0.9"
BLD_DIR="build"
VMPATH=/opt/ship/FairShip/build

bold() {
  echo -e "\033[1m$*\033[0m"
}

[ -n "$1" ] && TAG=$1 && shift
[ -n "$1" ] && DOCKER_USER=$1 && shift
[ -d "$1" ] && BLD_DIR=$1 && shift

REPO="$DOCKER_USER/ship-dev"

docker images | grep $REPO | grep $TAG -q
if [ $? -eq 0 ] ; then
  echo "ERR: name '$REPO:$TAG' is already taken"
  exit 1
fi

RESTORE_LINKS=""
for d in gconfig geometry python macro muonShieldOptimization ; do
  echo "copy $d -> $BLD_DIR"
  [ -d $BLD_DIR/$d ] && rm -rf $BLD_DIR/$d
  cp -r $d $BLD_DIR
  RESTORE_LINKS+=" $d"
done

path=$(readlink -f $BLD_DIR)

cat > $path/Dockerfile << EOF
FROM busybox
MAINTAINER Andrey Ustyuzhanin andrey.ustyuzhanin@cern.ch
WORKDIR $VMPATH

ADD . $VMPATH

EOF
docker build --rm -t $REPO:$TAG $path
pushd $BLD_DIR
for d in $RESTORE_LINKS ; do rm -rf $d ; ln -s ../$d . ;  done
popd
REPO_NAME_B=`bold "$REPO:$TAG"`
echo -e "You have just created container: " $REPO_NAME_B
echo -e "to check  it:"
echo -e "  docker run -ti --rm $REPO_NAME_B ls -l ."
echo -e "to push it to docker registry:"
echo -e "  docker push $REPO_NAME_B"
