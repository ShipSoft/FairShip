#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "MuonBackGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt

// read events from Pythia8/Geant4 base simulation (only target + hadron absorber

// -----   Default constructor   -------------------------------------------
MuonBackGenerator::MuonBackGenerator() {}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName) {
  fLogger = FairLogger::GetLogger();  
  fLogger->Info(MESSAGE_ORIGIN,"Opening input file %s",fileName);
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");  
  }
  fTree = (TTree *)fInputFile->Get("pythia8-Geant4");
  fNevents = fTree->GetEntries();
  fn = 0;
  fTree->SetBranchAddress("id",&id);                // particle id
  fTree->SetBranchAddress("parentid",&parentid);    // parent id, could be different   
  fTree->SetBranchAddress("pythiaid",&pythiaid);    // pythiaid original particle
  fTree->SetBranchAddress("ecut",&pythiaid);    // energy cut used in simulation
  fTree->SetBranchAddress("w",&w);                  // weight of event    
  fTree->SetBranchAddress("x",&vx);   // position
  fTree->SetBranchAddress("y",&vy);    
  fTree->SetBranchAddress("z",&vz);   
  fTree->SetBranchAddress("px",&px);   // momentum
  fTree->SetBranchAddress("py",&py);
  fTree->SetBranchAddress("pz",&pz);
  return kTRUE;
}
// -----   Destructor   ----------------------------------------------------
MuonBackGenerator::~MuonBackGenerator() 
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t MuonBackGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  while (fn<fNevents) {
   fTree->GetEntry(fn);
   fn++;
   if (fn %10000==0)  {fLogger->Info(MESSAGE_ORIGIN,"reading event %i",fn);}
// test if we have a muon, don't look at neutrinos:
   if (abs(int(id))==13) {break;}
  } 
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t mass = pdgBase->GetParticle(id)->Mass();
  Double_t    e = TMath::Sqrt( px*px+py*py+pz*pz+mass*mass );
  Double_t tof = 0; 
  cpg->AddTrack(int(id),px,py,pz,vx*100.,vy*100.,vz*100.,-1.,true,e,tof,w);   
  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t MuonBackGenerator::GetNevents()
{
 return fNevents;
}
void MuonBackGenerator::CloseFile()
{
 fInputFile->Close();
 fInputFile->Delete(); 
 delete fInputFile;
}

ClassImp(MuonBackGenerator)
