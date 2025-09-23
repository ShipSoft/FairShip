#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "MyGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt

using std::cout;
using std::endl;
// read events from ntuples produced

// -----   Default constructor   -------------------------------------------
MyGenerator::MyGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t MyGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t MyGenerator::Init(const char* fileName, const int firstEvent) {
  cout << "Info MyGenerator: Opening input file " << fileName << endl;
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    cout << "-E MyGenerator: Error opening the Signal file" << fileName << endl;
  }
  fTree = (TTree *)fInputFile->Get("mytree");
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  fTree->SetBranchAddress("pdgcode",&id);                // particle id
  fTree->SetBranchAddress("vx",&vx);   // position
  fTree->SetBranchAddress("vy",&vy);
  fTree->SetBranchAddress("vz",&vz);
  fTree->SetBranchAddress("px",&px);   // momentum
  fTree->SetBranchAddress("py",&py);
  fTree->SetBranchAddress("pz",&pz);
  cout << "Init OK" << fn << " " << fNevents << endl;
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
MyGenerator::~MyGenerator()
{
 // cout << "destroy My" << endl;
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t MyGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  cout <<fNevents<<endl;
  if (fn<fNevents) {
   fTree->GetEntry(fn);
   fn++;
   cout << "reading event "<<fn<<endl;
  }
  if (fn>=fNevents) {
     cout << "No more input events"<<endl;
     //return kFALSE;
  }

  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t mass = pdgBase->GetParticle(id)->Mass();
  Double_t    e = TMath::Sqrt( px*px+py*py+pz*pz+ mass*mass );
  cpg->AddTrack(id, px, py, pz, vx, vy, vz);
  cout << vx<< " " << vy<< " " << vz<<endl;

  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t MyGenerator::GetNevents()
{
 return fNevents;
}
