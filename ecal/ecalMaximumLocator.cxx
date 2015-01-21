#include "ecalMaximumLocator.h"

#include "ecalStructure.h"
#include "ecalInf.h"
#include "ecalMaximum.h"
#include "ecalCell.h"

#include "FairRootManager.h"

#include "TClonesArray.h"

#include <list>
#include <iostream>

using namespace std;

ecalMaximumLocator::ecalMaximumLocator()
  : FairTask(),
    fMaximums(NULL),
    fStr(NULL),
    fECut(0.015),
    fEvent(-1)
{
}

ecalMaximumLocator::ecalMaximumLocator(const char* name, Int_t verbose)
  : FairTask(name, verbose),
    fMaximums(NULL),
    fStr(NULL),
    fECut(0.015),
    fEvent(-1)
{
}

ecalMaximumLocator::~ecalMaximumLocator()
{
  if (fMaximums)
    delete fMaximums;
}

InitStatus ecalMaximumLocator::Init()
{
  FairRootManager* fManager=FairRootManager::Instance();
  if (!fManager)
  {
    Fatal("Init", "Can't find a Root Manager.");
    return kFATAL;
  }
  fStr=(ecalStructure*)fManager->GetObject("EcalStructure");
  if (!fStr)
  {
    Fatal("Init()", "Can't find calorimeter structure in the system.");
    return kFATAL;
  }
  fMaximums=new TClonesArray("ecalMaximum", 3000);
  fManager->Register("EcalMaximums", "ECAL", fMaximums, kFALSE);
  fEvent=0;
  return kSUCCESS;
}

TClonesArray* ecalMaximumLocator::InitPython(ecalStructure* structure)
{
  fStr=structure;
  fMaximums=new TClonesArray("ecalMaximum", 3000);
  return fMaximums;
}

void ecalMaximumLocator::Finish()
{
  fMaximums->Clear();
}

void ecalMaximumLocator::Exec(const Option_t* opt)
{
  list<ecalCell*> all;
  list<ecalCell*> cells;
  list<ecalCell*>::const_iterator p;
  list<ecalCell*>::const_iterator r;
  Double_t e;
  Double_t z=fStr->GetEcalInf()->GetZPos();
  Double_t r1;
  Double_t r2;
  Double_t t;
  Int_t n=0;

  fEvent++;
  fMaximums->Clear();
  fStr->GetCells(all);
  for(p=all.begin();p!=all.end();++p)
  {
    e=(*p)->GetEnergy();
    r1=(*p)->GetCenterX(); r1*=r1;
    t=(*p)->GetCenterY(); t*=t;
    r1=TMath::Sqrt(r1*r1+t*t);
    if (e<fECut)
      continue;
    (*p)->GetNeighborsList(cells);
    for(r=cells.begin();r!=cells.end();++r)
    {
      if ((*r)->GetEnergy()<e) continue;
      if ((*r)->GetEnergy()==e)
      {
        r2=(*r)->GetCenterX(); r2*=r2;
        t=(*r)->GetCenterY(); t*=t;
        r2=TMath::Sqrt(r2*r2+t*t);
	if (r1>=r2) continue;
      }
      break;
    }
    if (r!=cells.end())
      continue;
//    cout << e << " : " << (*p)->GetCenterX() << ", " << (*p)->GetCenterY() << endl;
    new ((*fMaximums)[n++]) ecalMaximum(*p, z);
  }
  if (fVerbose>9)
    Info("Exec", "%d maximums found", n);
}

ClassImp(ecalMaximumLocator)
