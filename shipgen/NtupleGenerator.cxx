#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "NtupleGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt

using std::cout;
using std::endl;
// read events from ntuples produced

// -----   Default constructor   -------------------------------------------
NtupleGenerator::NtupleGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t NtupleGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t NtupleGenerator::Init(const char* fileName, const int firstEvent) {
  cout << "Info NtupleGenerator: Opening input file " << fileName << endl;
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    cout << "-E NtupleGenerator: Error opening the Signal file" << fileName << endl;
  }
  fTree = (TTree *)fInputFile->Get("ntuple");
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  fTree->SetBranchAddress("id",&id);                // particle id
  if (fTree->FindBranch("parentid") ){ fTree->SetBranchAddress("parentid",&parentid);}    // parent id
  if (fTree->FindBranch("tof")      ){ fTree->SetBranchAddress("tof",&tof);}    // time of flight
  fTree->SetBranchAddress("Nmeas",&Nmeas);          // number of Geant4 points
  fTree->SetBranchAddress("Ezero",&Ezero);          // incoming muon energy
  fTree->SetBranchAddress("w",&w);                  // weight of event
  fTree->SetBranchAddress("x",&vx);   // position
  fTree->SetBranchAddress("y",&vy);
  fTree->SetBranchAddress("z",&vz);
  fTree->SetBranchAddress("px",&px);   // momentum
  fTree->SetBranchAddress("py",&py);
  fTree->SetBranchAddress("pz",&pz);
  fTree->SetBranchAddress("volid",&volid);     // which volume
  fTree->SetBranchAddress("procid",&procid);   // which process
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
NtupleGenerator::~NtupleGenerator()
{
 // cout << "destroy Ntuple" << endl;
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t NtupleGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  while (fn<fNevents) {
   fTree->GetEntry(fn);
   fn++;
   if (fn %10000==0)  {cout << "reading event "<<fn<<endl;}
// test if muon survives:
   Int_t i = Nmeas-3;
   Float_t r2 = (vx[i]*vx[i]+vy[i]*vy[i]);
   if (procid[Nmeas-1]==2&&r2<9) {break;}
  }
  if (fn==fNevents) {
     cout << "No more input events"<<endl;
     return kFALSE; }
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t mass = pdgBase->GetParticle(id)->Mass();
  Double_t    e = TMath::Sqrt( px[0]*px[0]+py[0]*py[0]+pz[0]*pz[0]+ mass*mass );
  tof = 0;
// first, original muon
  cpg->AddTrack(id,px[0],py[0],pz[0],vx[0]*100.,vy[0]*100.,vz[0]*100.,-1.,false,e,tof,w);
  Int_t i = Nmeas-1;
// second, surviving muon, extrapolate back to end of muon shield, z=20m
  Double_t zscor = 20.;
  Double_t lam = (zscor-vz[i])/pz[i];
  Double_t xscor = vx[i]+lam*px[i];
  Double_t yscor = vy[i]+lam*py[i];
  e = TMath::Sqrt( px[i]*px[i]+py[i]*py[i]+pz[i]*pz[i]+ mass*mass );
  cpg->AddTrack(id,px[i],py[i],pz[i],xscor*100.,yscor*100.,zscor*100.,0,true,e,tof,w);
  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t NtupleGenerator::GetNevents()
{
 return fNevents;
}


ClassImp(NtupleGenerator)
