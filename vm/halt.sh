mode=poweroff
[ -n "$1" ] && mode=$1
uuid=`VBoxManage list runningvms | grep 'FairShip' | awk '{print $2}'| sed s/[{}]//g`
if [ -n "$uuid" ] ; then
  VBoxManage controlvm $uuid $mode
else
  echo "No FairShip VM seems to be running"
fi
