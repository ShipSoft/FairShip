#include "ecalMatch.h"

#include "ecalCellMC.h"
#include "ecalStructure.h"
#include "ecalReconstructed.h"

#include "ShipMCTrack.h"

#include "TClonesArray.h"

#include <iostream>
#include <list>
#include <map>

using namespace std;

void ecalMatch::Exec(Option_t* option,TClonesArray* reconstructed,TClonesArray* mctracks)
{
  fReconstucted=reconstructed;
  fMCTracks=mctracks;
  fEv++; fN=0; fRejected=0;

  Int_t n=fReconstucted->GetEntries();
  Int_t i;
  ecalReconstructed* rc;
  ecalCell* cell;
  ecalCellMC* mccell;
  list<ecalCell*> cells;
  list<ecalCell*>::const_iterator p;
  map<Int_t, Float_t> e;
  map<Int_t, Float_t> e2;
  map<Int_t, Float_t>::const_iterator ep;
  map<Int_t, Float_t>::reverse_iterator rp;
  ShipMCTrack* tr;
  Int_t trn;
  Float_t max;
//  if (fVerbose>0) Info("Exec", "Event %d.", fEv);
  for(i=0;i<n;i++)
  {
    rc=(ecalReconstructed*)fReconstucted->At(i);
    cell=fStr->GetHitCell(rc->CellNum());
    cells.clear();

    if (fUse3x3)
    {
      cell->GetNeighborsList(cells); //3x3 without maximum
      cells.push_back(cell);
    }
    else
      cell->Get5x5Cluster(cells);

    e.clear(); e2.clear();
    //Counting energy depositions for all particles
    for(p=cells.begin();p!=cells.end();++p)
    {
      mccell=(ecalCellMC*)(*p);
      for(ep=mccell->GetTrackEnergyBegin();ep!=mccell->GetTrackEnergyEnd();++ep)
      {
	if (e.find(ep->first)==e.end())
	  e[ep->first]=ep->second;
	else
	  e[ep->first]+=ep->second;
      }
    }

    //...and parent photons and electrons/positrons
    for(ep=e.begin();ep!=e.end();++ep)
    {
      if (e2.find(ep->first)==e.end())
	e2[ep->first]=ep->second;
      else
	e2[ep->first]+=ep->second;
      if (ep->first<0&&fVerbose==0) continue;
      tr=(ShipMCTrack*)fMCTracks->At(ep->first);
      if (tr==NULL)
      {
	Info("Exec", "Event %d. Can't find MCTrack %d.", fEv, ep->first);
	continue;
      }
      for(;;)
      {
	if (tr->GetPdgCode()!=22&&TMath::Abs(tr->GetPdgCode())!=11) break;
	trn=tr->GetMotherId();
	if (trn<0) break;
	tr=(ShipMCTrack*)fMCTracks->At(trn);
	if (tr==NULL)
	{
	  Info("Exec", "Event %d. Can't find MCTrack %d.", fEv, ep->first);
	  break;
	}
	if (tr->GetPdgCode()!=22&&TMath::Abs(tr->GetPdgCode())!=11) break;
	if (e2.find(trn)==e2.end())
	  e2[trn]=ep->second;
	else
	  e2[trn]+=ep->second;
      }
    }

    //Maximum location
    max=-1e11; trn=-1111;
    for(rp=e2.rbegin();rp!=e2.rend();++rp)
    {
      if (rp->second>max)
	{ max=rp->second; trn=rp->first;}
    }

    if (trn>=0)
    {
      rc->SetMCTrack(trn);
      fN++;
    }
    else
      fRejected++;
  }

  if (fVerbose>0) Info("Exec", "Event %d. Matched %d. Skipped %d maxs.", fEv, fN, fRejected);
}

/** Standard constructor **/
ecalMatch::ecalMatch(const char* name, const Int_t verbose)
  : FairTask(name, verbose), fEv(0), fN(0), fRejected(0), fUse3x3(0), 
    fReconstucted(NULL), fMCTracks(NULL), fStr(NULL) 
{
  ;
}

/** Only to comply with frame work. **/
ecalMatch::ecalMatch()
  : FairTask(), fEv(0), fN(0), fRejected(0), fUse3x3(0), 
    fReconstucted(NULL), fMCTracks(NULL), fStr(NULL)
{
  ;
}

/** Finish a task **/
void ecalMatch::Finish()
{
  ;
}

/** Destructor **/
ecalMatch::~ecalMatch()
{
  ;
}

InitStatus ecalMatch::Init()
{
  FairRootManager* io=FairRootManager::Instance();
  if (!io)
  {
    Fatal("Init", "Can't find IOManager.");
    return kFATAL;
  }
  fStr=(ecalStructure*)io->GetObject("EcalStructure");
  if (!fStr) 
  {
    Fatal("Init()", "Can't find calorimeter structure in the system.");
    return kFATAL;
  }
  fReconstucted=(TClonesArray*)io->GetObject("EcalReco");
  if (!fReconstucted)
  {
    Fatal("Init", "Can't find array of reconstructed calorimeter objects in the system.");
    return kFATAL;
  }
  fMCTracks=(TClonesArray*)io->GetObject("MCTrack");
  if (!fMCTracks)
  {
    Fatal("Init", "Can't find array of MC tracks in the system.");
    return kFATAL;
  }

  fEv=0;
  return kSUCCESS;
}

void ecalMatch::InitPython(ecalStructure* str, TClonesArray* reconstructed, TClonesArray* mctracks)
{
  fStr=str;
  fReconstucted=reconstructed;
  fMCTracks=mctracks;
  
  fEv=0;
}

ClassImp(ecalMatch)
