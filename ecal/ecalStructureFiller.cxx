#include "ecalStructureFiller.h"
#include "ecalPoint.h"
#include "ecalCellMC.h"
#include "ecalInf.h"
#include "ecalStructure.h"

#include "FairRootManager.h"

#include "TRandom.h"
#include "TVector3.h"
#include "TClonesArray.h"

#include <vector>
#include <iostream>

using namespace std;

// -----   Default constructor   -------------------------------------------
ecalStructureFiller::ecalStructureFiller() 
  : FairTask(), 
    fStr(NULL),
    fInf(NULL),
    fListECALpts(NULL),
    fEvent(0),
    fInited(kFALSE),
    fUseMCPoints(kFALSE),
    fStoreTrackInfo(kTRUE),
    fFileGeo("")
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   -------------------------------------------
ecalStructureFiller::ecalStructureFiller(const char *name, const Int_t iVerbose, const char* fileGeo) 
  : FairTask(name,iVerbose),
    fStr(NULL),
    fInf(ecalInf::GetInstance(fileGeo)),
    fListECALpts(NULL),
    fEvent(0),
    fInited(kFALSE),
    fUseMCPoints(kFALSE),
    fStoreTrackInfo(kTRUE),
    fFileGeo(fileGeo)
{
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
ecalStructureFiller::~ecalStructureFiller()
{
  ;
}
// -------------------------------------------------------------------------

void ecalStructureFiller::SetParContainers()
{
  ;
}

// -----   Initialization   ------------------------------------------------
InitStatus ecalStructureFiller::Init()
{
  fInited=kTRUE;
  FairRootManager* fManager = FairRootManager::Instance();

  if (fUseMCPoints==kFALSE)
  {
    Warning("Init()", "No data source for structure filler! Calorimeter structure will be empty.");
//    return kFATAL;
  }
  //ECAL MC points
  if (fUseMCPoints) 
    fListECALpts = (TClonesArray*)fManager->GetObject("EcalPointLite");

  //fInf->CheckVariables();
  fStr=new ecalStructure(fInf);
  if (fStoreTrackInfo) fStr->SetUseMC(1);
  fStr->Construct();
  
  fManager->Register("EcalStructure", "ECAL", fStr, kFALSE);
  return kSUCCESS;
}
// -------------------------------------------------------------------------


ecalStructure* ecalStructureFiller::InitPython(TClonesArray* litePoints)
{
  fListECALpts=litePoints;

  //fInf->CheckVariables();
  fStr=new ecalStructure(fInf);
  if (fStoreTrackInfo) fStr->SetUseMC(1);
  fStr->Construct();

  return fStr;
}


/** Loop over MCPoints hits and add them to cells **/
void ecalStructureFiller::LoopForMCPoints()
{
  ecalPoint* pt;
  ecalCell* cell;
  Int_t ten;
  UInt_t n;
  Bool_t isPS;

  n=fListECALpts->GetEntriesFast();
  if (fVerbose>0)
  {
    cout << ". Number of input MC points: ";
    cout << n << flush;
  }

  for(UInt_t j=0; j<n; j++)
  {
    pt=(ecalPoint*)fListECALpts->At(j);
    cell=fStr->GetCell(pt->GetDetectorID(), ten, isPS);
    if (ten==0) {
      if (isPS)
        ; // cell->AddPSEnergy(pt->GetEnergyLoss()); preshower removed
      else
        cell->AddEnergy(pt->GetEnergyLoss());
    }
  }
  if (fStoreTrackInfo)
  for(UInt_t j=0; j<n; j++)
  {
    pt=(ecalPoint*)fListECALpts->At(j);
    ecalCellMC* cellmc=(ecalCellMC*)fStr->GetCell(pt->GetDetectorID(), ten, isPS);
    if (ten==0) {
      if (isPS)
        ; // cell->AddTrackPSEnergy(pt->GetTrackID(),pt->GetEnergyLoss()); //preshower removed
      else
        cellmc->AddTrackEnergy(pt->GetTrackID(),pt->GetEnergyLoss(), pt->GetTime());
    }
  }
}

// -----   Execution of Task   ---------------------------------------------
void ecalStructureFiller::Exec(Option_t* option,TClonesArray* litePoints)
{
  fEvent++;
  fListECALpts=litePoints;
  if (fVerbose>0)
    cout << "--> Event no. " << fEvent;

  fStr->ResetModules();
  if (fUseMCPoints) LoopForMCPoints();

  if (fVerbose>0)
    cout << endl << flush;
}
// -------------------------------------------------------------------------


// -----   Finish Task   ---------------------------------------------------
void ecalStructureFiller::Finish()
{
  ;
}
// -------------------------------------------------------------------------


ClassImp(ecalStructureFiller)
