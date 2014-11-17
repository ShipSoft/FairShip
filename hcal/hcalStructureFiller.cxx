#include "hcalStructureFiller.h"
#include "hcalPoint.h"
#include "hcalModuleMC.h"
#include "hcalInf.h"
#include "hcalStructure.h"

#include "FairRootManager.h"

#include "TRandom.h"
#include "TVector3.h"
#include "TClonesArray.h"

#include <vector>
#include <iostream>

using namespace std;

// -----   Default constructor   -------------------------------------------
hcalStructureFiller::hcalStructureFiller() 
  : FairTask(), 
    fStr(NULL),
    fInf(NULL),
    fListHCALpts(NULL),
    fEvent(0),
    fInited(kFALSE),
    fUseMCPoints(kFALSE),
    fStoreTrackInfo(kTRUE),
    fFileGeo("")
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   -------------------------------------------
hcalStructureFiller::hcalStructureFiller(const char *name, const Int_t iVerbose, const char* fileGeo) 
  : FairTask(name,iVerbose),
    fStr(NULL),
    fInf(hcalInf::GetInstance(fileGeo)),
    fListHCALpts(NULL),
    fEvent(0),
    fInited(kFALSE),
    fUseMCPoints(kFALSE),
    fStoreTrackInfo(kTRUE),
    fFileGeo(fileGeo)
{
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
hcalStructureFiller::~hcalStructureFiller()
{
  ;
}
// -------------------------------------------------------------------------

void hcalStructureFiller::SetParContainers()
{
  ;
}

// -----   Initialization   ------------------------------------------------
InitStatus hcalStructureFiller::Init()
{
  fInited=kTRUE;
  FairRootManager* fManager = FairRootManager::Instance();

  if (fUseMCPoints==kFALSE)
  {
    Warning("Init()", "No data source for structure filler! Calorimeter structure will be empty.");
//    return kFATAL;
  }
  //HCAL MC points
  if (fUseMCPoints) 
    fListHCALpts = (TClonesArray*)fManager->GetObject("HcalPointLite");

  //fInf->CheckVariables();
  fStr=new hcalStructure(fInf);
  if (fStoreTrackInfo) fStr->SetUseMC(1);
  fStr->Construct();
  
  fManager->Register("HcalStructure", "HCAL", fStr, kFALSE);
  return kSUCCESS;
}
// -------------------------------------------------------------------------

/** Loop over MCPoints hits and add them to modules **/
void hcalStructureFiller::LoopForMCPoints()
{
  hcalPoint* pt=NULL;
  hcalModule* module;
  UInt_t n;
  Int_t section;

  n=fListHCALpts->GetEntriesFast();
  if (fVerbose>0)
  {
    cout << ". Number of input MC points: ";
    cout << n << flush;
  }

  for(UInt_t j=0; j<n; j++)
  {
    pt=(hcalPoint*)fListHCALpts->At(j);
    module=fStr->GetModule(pt->GetDetectorID(), section);
    cout << section << " " << pt->GetEnergyLoss() << endl;
    if (section==0)
      module->AddEnergy(pt->GetEnergyLoss());
    else
      module->AddEnergy2(pt->GetEnergyLoss());
  }
  if (fStoreTrackInfo)
  for(UInt_t j=0; j<n; j++)
  {
    pt=(hcalPoint*)fListHCALpts->At(j);
    hcalModuleMC* modulemc=(hcalModuleMC*)fStr->GetModule(pt->GetDetectorID(), section);
    if (section==0)
      modulemc->AddTrackEnergy(pt->GetTrackID(),pt->GetEnergyLoss());
    else
      modulemc->AddTrackEnergy2(pt->GetTrackID(),pt->GetEnergyLoss());
  }
}

// -----   Execution of Task   ---------------------------------------------
void hcalStructureFiller::Exec(Option_t* option)
{
  fEvent++;
  if (fVerbose>0)
    cout << "--> Event no. " << fEvent;

  fStr->ResetModules();
  if (fUseMCPoints) LoopForMCPoints();

  if (fVerbose>0)
    cout << endl << flush;
}
// -------------------------------------------------------------------------


// -----   Finish Task   ---------------------------------------------------
void hcalStructureFiller::Finish()
{
  ;
}
// -------------------------------------------------------------------------


ClassImp(hcalStructureFiller)
