#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "ALPACAGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt

const Double_t cm = 10.; // pythia units are mm
const Double_t c_light = 2.99792458e+10; // speed of light in cm/sec (c_light   = 2.99792458e+8 * m/s)

using std::cout;
using std::endl;
// read events from ntuples produced

// -----   Default constructor   -------------------------------------------
ALPACAGenerator::ALPACAGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t ALPACAGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t ALPACAGenerator::Init(const char* fileName, const int firstEvent) {
  cout << "Info ALPACAGenerator: Opening input file " << fileName << endl;
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    cout << "-E ALPACAGenerator: Error opening the Signal file" << fileName << endl;
  }
  fTree = (TTree *)fInputFile->Get("MCTrack");
  fNevents = fTree->GetEntries();
  fn=firstEvent;
  fTree->SetBranchAddress("event",&event); //event no.
  fTree->SetBranchAddress("track",&track); //track no.
  fTree->SetBranchAddress("pdg",&pdg);              // particle pdg
  fTree->SetBranchAddress("parent",&parent);    // parent track number
  fTree->SetBranchAddress("tof",&tof); // time of flight
  fTree->SetBranchAddress("e",&e);          // incoming muon energy
  fTree->SetBranchAddress("w",&w);                  // weight of event
  fTree->SetBranchAddress("x",&x); // position in x
  fTree->SetBranchAddress("y",&y); // position in y
  fTree->SetBranchAddress("z",&z); // position in z
  fTree->SetBranchAddress("px",&px);     // momentum in x
  fTree->SetBranchAddress("py",&py);     // momentum in y
  fTree->SetBranchAddress("pz",&pz);     // momentum in z
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
ALPACAGenerator::~ALPACAGenerator()
{
 // cout << "destroy Ntuple" << endl;
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t ALPACAGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  if (fn<fNevents) {
  fTree->GetEntry(fn); // ALP is getting,
  if (track==0&&parent==-1) {
      cpg->AddTrack(pdg,px,py,pz,x,y,z,-1.,false,e,tof,w); // ALP track is added.
  }
  fTree->GetEntry(fn+1); // First daughter/photon is getting,
  if (track==1&&parent==0) {
      cpg->AddTrack(pdg,px,py,pz,x,y,z,0,true,e,tof,w); // First daughter/photon track is added.
  }
  fTree->GetEntry(fn+2); // Second daughter/photon is getting,
  if (track==2&&parent==0) {
      cpg->AddTrack(pdg,px,py,pz,x,y,z,0,true,e,tof,w); // Second daughter/photon track is added.
  }
  else {
      return kFALSE;
  }
  fn=fn+3; // Goes to next event, more specifically next ALP,
  cout << "Event Number:"<<fn/3 <<endl; // this division is due to the fact that ntuple is recorded in track based and every event has three tracks.
  return kTRUE;
  }
  else {
     cout << "No more input events"<<endl;
     return kFALSE;
  }
}


// -------------------------------------------------------------------------
Int_t ALPACAGenerator::GetNevents()
{
 return fNevents/3;
}


ClassImp(ALPACAGenerator)
