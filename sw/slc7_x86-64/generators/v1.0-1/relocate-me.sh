#!/bin/bash -e
if [[ "$WORK_DIR" == '' ]]; then
  echo 'Please, define $WORK_DIR'
  exit 1
fi
OP=slc7_x86-64/generators/v1.0-1
PP=${PKGPATH:-slc7_x86-64/generators/v1.0-1}
PH=8b3b9cc4aa41af88ceb775c4c1ac8ecdfec3a437
sed -e "s|/[^ ;:]*INSTALLROOT/$PH/$OP|$WORK_DIR/$PP|g;s|[@][@]PKGREVISION[@]$PH[@][@]|1|g" $PP/etc/profile.d/init.sh.unrelocated > $PP/etc/profile.d/init.sh
