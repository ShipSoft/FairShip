SCRIPT_NAME=$0
[[ -z "SCRIPT_NAME" || "$SCRIPT_NAME" == "bash" ]] && SCRIPT_NAME=$BASH_SOURCE
VM_DIR=`dirname "$SCRIPT_NAME"`
source $VM_DIR/_functions.sh

IMAGE="anaderi/fairroot:latest"
