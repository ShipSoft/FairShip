#include "ecalClusterCalibration.h"

#include "FairRootManager.h"

#include "TFormula.h"

#include <iostream>
#include <fstream>
#include <list>

using namespace std;

/** --- Default constructor --------------------------------------------------- **/
ecalClusterCalibration::ecalClusterCalibration() 
  : FairTask("EcalClusterCalibration", 0)
{
  Int_t i;

  for(i=0;i<10;i++)
    fStraightCalibration[i]=fCalibration[i]=NULL;
}

/** --- Standard constructor. Use this ---------------------------------------- **/
ecalClusterCalibration::ecalClusterCalibration(const char* name, Int_t iVerbose)
  : FairTask(name, iVerbose)
{
  Int_t i;

  for(i=0;i<10;i++)
    fStraightCalibration[i]=fCalibration[i]=NULL;
}

/** --- Calibration if only cluster energy is known --------------------------- **/
Double_t ecalClusterCalibration::Calibrate(Int_t celltype, Double_t energy)
{
  if (fStraightCalibration[celltype]==NULL)
  {
    Error("Calibrate", "No straight calibration for celltype %d.", celltype);
    return -1111;
  }
  return fStraightCalibration[celltype]->Eval(energy);
}

/** --- Calibration if theta and cluster energy is known ---------------------- **/
Double_t ecalClusterCalibration::Calibrate(Int_t celltype, Double_t energy, Double_t theta)
{
  if (fCalibration[celltype]==NULL)
  {
    Error("Calibrate", "No calibration for celltype %d.", celltype);
    return -1111;
  }
  return fCalibration[celltype]->Eval(energy, theta);
}

/** --- Initialization of the task -------------------------------------------- **/
InitStatus ecalClusterCalibration::Init()
{
  FairRootManager* manager=FairRootManager::Instance();
  if (!manager)
  {
    Fatal("Init()", "Can't find IOManager.");
    return kFATAL;
  }

  manager->Register(GetName(), "ECAL", this, kFALSE);
  
  return kSUCCESS;
}

/** --- Executed task --------------------------------------------------------- **/ 
void ecalClusterCalibration::Exec(Option_t* option)
{
  ;
}

/** --- Finish task ----------------------------------------------------------- **/ 
void ecalClusterCalibration::Finish()
{
  ;
}
/** --- Destructor ------------------------------------------------------------ **/
ecalClusterCalibration::~ecalClusterCalibration()
{
  ;
}

ClassImp(ecalClusterCalibration)
