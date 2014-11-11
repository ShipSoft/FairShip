# for setup at CERN lxplus
setenv mySHIPSOFT /afs/cern.ch/ship/sw/ShipSoft
setenv SHIPSOFT /afs/cern.ch/ship/sw/ShipSoft
setenv SIMPATH  ${SHIPSOFT}/FairSoftInst
setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
setenv FAIRSHIP ${SHIPSOFT}/FairShip
source ${mySHIPSOFT}/FairShipRun/config.csh
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/opt/rh/python27/root/usr/lib64
