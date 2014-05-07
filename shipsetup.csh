# for setup at CERN lxplus
setenv SHIPSOFT /afs/cern.ch/ship/sw/ShipSoft
setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
setenv SIMPATH  ${SHIPSOFT}/withPython/FairSoftInst
source ${SHIPSOFT}/FairShipRun/config.csh
setenv PYTHONPATH ${PYTHONPATH}:${SHIPSOFT}/withPython/FairSoft/tools/root/bindings/pyroot:${SIMPATH}/lib
setenv PYTHONPATH ${PYTHONPATH}:${SIMPATH}/lib/root
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/opt/rh/python27/root/usr/lib64

setenv PYTHONPATH ${PYTHONPATH}:${SHIPSOFT}/FairShip/python

# wants to look for /afs/cern.ch/ship/sw/ShipSoft/withPython/FairSoftInst/lib64 
# too stupid, the libraries are in /afs/cern.ch/ship/sw/ShipSoft/withPython/FairSoftInst/lib
# ln -s  FairSoftInst/lib FairSoftInst/lib64
