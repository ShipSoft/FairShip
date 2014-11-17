#include "hcalAnalysisSimple.h"

#include "FairRootManager.h"

#include "hcalStructure.h"
#include "hcalModule.h"
#include "hcalPoint.h"

#include "TTree.h"
#include "TClonesArray.h"
#include "TRandom.h"

#include <iostream>
#include <fstream>
#include <list>

using namespace std;

/** Loop procedure **/
void hcalAnalysisSimple::Exec(Option_t* option)
{
  Int_t n=fTracks->GetEntries();
  Int_t i;
  hcalPoint* t;
  hcalModule* module;
  hcalModule* mmodule;
  TVector3 m;
  list<hcalModule*> modules;
  list<hcalModule*>::const_iterator p;
//  TVector3 m1;

  fEv++;
  InitTree();

  for(i=0;i<n;i++)
  {
    t=(hcalPoint*)fTracks->At(i);
    fX=t->GetX();
    fY=t->GetY();
    t->Momentum(m);
    fP=m.Mag();
    fPX=m.Px();
    fPY=m.Py();
    fPZ=m.Pz();

//    m1=m.Unit();
    module=fStr->GetModule(fX, fY);
    if (!module) continue;
    mmodule=module;
    module->GetNeighborsList(modules);
    for(p=modules.begin();p!=modules.end();++p)
      if ((*p)->GetEnergy()>mmodule->GetEnergy())
	mmodule=(*p);

    mmodule->GetNeighborsList(modules);
    for(p=modules.begin();p!=modules.end();++p)
      if ((*p)->GetEnergy()>mmodule->GetEnergy())
	break;

    if (p!=modules.end()) continue;

    fCX=mmodule->GetCenterX();
    fCY=mmodule->GetCenterY();
    fCE=mmodule->GetEnergy();
    fCE2=mmodule->GetEnergy2();
    fModuleNum=mmodule->GetNumber();
    fADC=mmodule->ADC();
    fOE=fCE;
    for(p=modules.begin();p!=modules.end();++p)
      fOE+=(*p)->GetEnergy();

    fTree->Fill();
  }

}

void hcalAnalysisSimple::InitTree()
{
  if (fTree) return;
  fTree=new TTree("calib", "calib");
  fTree->Branch("px", &fPX, "px/D");
  fTree->Branch("py", &fPY, "py/D");
  fTree->Branch("pz", &fPZ, "pz/D");
  fTree->Branch("p" , &fP , "p/D");
  fTree->Branch("x" , &fX , "x/D");
  fTree->Branch("y" , &fY , "y/D");
  fTree->Branch("cx", &fCX, "cx/D");
  fTree->Branch("cy", &fCY, "cy/D");
  fTree->Branch("ce", &fCE, "ce/D");
  fTree->Branch("ce2",&fCE2,"ce2/D");
  fTree->Branch("oe", &fOE, "oe/D");
  fTree->Branch("ev", &fEv, "ev/I");
  fTree->Branch("mn", &fModuleNum, "mn/I");
  fTree->Branch("adc", &fADC, "adc/I");
}

hcalAnalysisSimple::hcalAnalysisSimple(const char* name, const Int_t iVerbose)
  : FairTask(name, iVerbose),
    fTree(NULL),
    fX(0.),
    fY(0.),
    fCX(0.),
    fCY(0.),
    fP(0.),
    fCE(0.),
    fCE2(0.),
    fOE(0.),
    fPX(0.),
    fPY(0.),
    fPZ(0.),
    fEv(0),
    fModuleNum(0),
    fADC(0),
    fStr(NULL),
    fTracks(NULL)
{
}

hcalAnalysisSimple::hcalAnalysisSimple()
  : FairTask(),
    fTree(NULL),
    fX(0.),
    fY(0.),
    fCX(0.),
    fCY(0.),
    fP(0.),
    fCE(0.),
    fCE2(0.),
    fOE(0.),
    fPX(0.),
    fPY(0.),
    fPZ(0.),
    fEv(0),
    fModuleNum(0),
    fADC(0),
    fStr(NULL),
    fTracks(NULL)
{
}

/** Initing routine **/
InitStatus hcalAnalysisSimple::Init()
{
  FairRootManager* fManager=FairRootManager::Instance();
  fStr=(hcalStructure*)fManager->GetObject("HcalStructure");
  if (!fStr)
  {
    Fatal("Init()", "Can't find calorimeter structure. ");
    return kFATAL;
  }
  fTracks=(TClonesArray*)fManager->GetObject("HcalPoint");
  if (!fTracks)
  {
    Fatal("Init()", "Can't find array of reconstructed tracks. ");
    return kFATAL;
  }

  return kSUCCESS;
}

/** Finishing routine **/
void hcalAnalysisSimple::Finish()
{
  if (fTree)
    fTree->Write();
}

ClassImp(hcalAnalysisSimple)
