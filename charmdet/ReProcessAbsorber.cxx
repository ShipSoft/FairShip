#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "TVector3.h"
#include "FairPrimaryGenerator.h"
#include "TMCProcess.h"
#include "ReProcessAbsorber.h"
#include "Track.h"
#include "MeasuredStateOnPlane.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt

using std::cout;
using std::endl;
// read fitted tracks from muflux data and pass through additional material

// -----   Default constructor   -------------------------------------------
ReProcessAbsorber::ReProcessAbsorber() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t ReProcessAbsorber::Init(const char* fileName) {
  cout << "Info ReProcessAbsorber: Opening input file " << fileName << endl;
  fInputFile  = TFile::Open(fileName);
  if (fInputFile->IsZombie()) {
    cout << "-E ReProcessAbsorber: Error opening the Signal file " << fileName << endl;
  }
  fTree    = (TTree *)fInputFile->Get("cbmsim");
  fNevents = fTree->GetEntries();
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  muMass = pdgBase->GetParticle(13)->Mass();
  FitTracks = new TClonesArray("genfit::Track");
  fTree->SetBranchAddress("FitTracks",&FitTracks);
  fn = 0;
  fZ = 0;
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
ReProcessAbsorber::~ReProcessAbsorber()
{
 // cout << "destroy Ntuple" << endl;
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t ReProcessAbsorber::ReadEvent(FairPrimaryGenerator* cpg)
{
  while (1>0) {
   if (fn==fNevents) {
     cout << "No more input events"<<endl;
     return kFALSE; }
   fTree->GetEntry(fn);
   if (fn %10000==0)  {cout << "reading event "<<fn<<endl;}
   fn++;
   for (Int_t i=0;i<FitTracks->GetEntriesFast();i++) {
       genfit::Track *atrack = (genfit::Track*)FitTracks->At(i);
       const genfit::MeasuredStateOnPlane fState =  atrack->getFittedState(0);
       int pdgCode = -int(13*fState.getCharge());
       TVector3 pos = fState.getPos();
       TVector3 mom = fState.getMom();
       Double_t E = TMath::Sqrt(mom.Mag2()+muMass*muMass);
       TMCProcess procID  = kPTransportation;
       cpg->AddTrack(pdgCode,mom[0],mom[1],mom[2],pos[0],pos[1],fZ, -1,kTrue,E, 0.,1.,procID);
   }
   if (FitTracks->GetEntriesFast()>0)break;
  }
  return kTRUE;

}

// -------------------------------------------------------------------------
Int_t ReProcessAbsorber::GetNevents()
{
 return fNevents;
}

ClassImp(ReProcessAbsorber)
