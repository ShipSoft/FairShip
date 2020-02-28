#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "AlpacaGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt

const Double_t cm = 10.; // pythia units are mm
const Double_t c_light = 2.99792458e+10; // speed of light in cm/sec (c_light   = 2.99792458e+8 * m/s)

using std::cout;
using std::endl;
// read events from ntuples produced

// -----   Default constructor   -------------------------------------------
AlpacaGenerator::AlpacaGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t AlpacaGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t AlpacaGenerator::Init(const char* fileName, const int firstEvent) {
  cout << "Info AlpacaGenerator: Opening input file " << fileName << endl;
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    cout << "-E AlpacaGenerator: Error opening the Signal file" << fileName << endl;
  }
  fTree = (TTree *)fInputFile->Get("MCTrack");
  fNevents = fTree->GetEntries();
  fn=firstEvent;
  fTree->SetBranchAddress("event",&event);
  fTree->SetBranchAddress("track",&track);
  fTree->SetBranchAddress("pdg",&pdg);              // particle pdg
  fTree->SetBranchAddress("parent",&parent);    // parent track number??
  fTree->SetBranchAddress("tof",&tof); // time of flight
  fTree->SetBranchAddress("e",&e);          // incoming muon energy
  fTree->SetBranchAddress("w",&w);                  // weight of event
  fTree->SetBranchAddress("x",&x); // position
  fTree->SetBranchAddress("y",&y);
  fTree->SetBranchAddress("z",&z);
  fTree->SetBranchAddress("px",&px);     // momentum
  fTree->SetBranchAddress("py",&py);
  fTree->SetBranchAddress("pz",&pz);
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
AlpacaGenerator::~AlpacaGenerator()
{
 // cout << "destroy Ntuple" << endl;
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t AlpacaGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  while (fn<fNevents) {
  fTree->GetEntry(fn);
  if (track==0&&parent==-1) {cpg->AddTrack(pdg,px,py,pz,x,y,z,-1.,false,e,tof,w);} //Be sure the order, units, and possible errors(i.e pdg/track_id)
  fTree->GetEntry(fn+1);
  if (track==1&&parent==0) {cpg->AddTrack(pdg,px,py,pz,x,y,z,0,true,e,tof,w);}
  fTree->GetEntry(fn+2);
  if (track==2&&parent==0) {cpg->AddTrack(pdg,px,py,pz,x,y,z,0,true,e,tof,w);}
  fn=fn+3;
  cout << "eee?"<<fn <<endl;
  break;
  }
  //if (fn==fNevents) {
     //cout << "No more input events"<<endl;
     //return kFALSE; }
  return kTRUE;
}


// -------------------------------------------------------------------------
Int_t AlpacaGenerator::GetNevents()
{
 return fNevents/3;
}


ClassImp(AlpacaGenerator)
