# for setup at CERN lxplus
setenv mySHIPSOFT /afs/cern.ch/user/e/evh/public/ShipSoft
setenv SHIPSOFT /afs/cern.ch/ship/sw/ShipSoft
setenv SIMPATH  ${SHIPSOFT}/FairSoftInst
setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
setenv FAIRSHIP ${SHIPSOFT}/FairShip
source ${mySHIPSOFT}/FairShipRun/config.csh
setenv PYTHONPATH ${PYTHONPATH}:${SHIPSOFT}/FairSoft/tools/root/bindings/pyroot:${SIMPATH}/lib
setenv PYTHONPATH ${PYTHONPATH}:${SIMPATH}/lib/root
setenv PYTHONPATH ${PYTHONPATH}:${mySHIPSOFT}/FairShip/python
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/opt/rh/python27/root/usr/lib64
