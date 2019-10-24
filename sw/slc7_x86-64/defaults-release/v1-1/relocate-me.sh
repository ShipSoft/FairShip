#!/bin/bash -e
if [[ "$WORK_DIR" == '' ]]; then
  echo 'Please, define $WORK_DIR'
  exit 1
fi
OP=slc7_x86-64/defaults-release/v1-1
PP=${PKGPATH:-slc7_x86-64/defaults-release/v1-1}
PH=399356a4e5c7bc2f4d66039426b2db344b37bcd0
sed -e "s|/[^ ;:]*INSTALLROOT/$PH/$OP|$WORK_DIR/$PP|g;s|[@][@]PKGREVISION[@]$PH[@][@]|1|g" $PP/etc/profile.d/init.sh.unrelocated > $PP/etc/profile.d/init.sh
