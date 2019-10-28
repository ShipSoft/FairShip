#!/bin/bash -e
if [[ "$WORK_DIR" == '' ]]; then
  echo 'Please, define $WORK_DIR'
  exit 1
fi
OP=slc7_x86-64/simulation/v1.0-1
PP=${PKGPATH:-slc7_x86-64/simulation/v1.0-1}
PH=07dfc6e33cac1c179c602988331328054030a13c
sed -e "s|/[^ ;:]*INSTALLROOT/$PH/$OP|$WORK_DIR/$PP|g;s|[@][@]PKGREVISION[@]$PH[@][@]|1|g" $PP/etc/profile.d/init.sh.unrelocated > $PP/etc/profile.d/init.sh
