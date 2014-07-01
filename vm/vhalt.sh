mode=poweroff
[ -n "$1" ] && mode=$1
uuid=`VBoxManage list runningvms | grep 'FairShip' | awk '{print $2}'| sed s/[{}]//g`
VBoxManage controlvm $uuid $mode
