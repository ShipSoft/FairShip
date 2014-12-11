#include <math.h>
#include "TROOT.h"
#include "TRandom.h"
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
 Init(fileName, 0, false); 
}
// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName, const int firstEvent, const Bool_t fl ) {
  fLogger = FairLogger::GetLogger();  
  fLogger->Info(MESSAGE_ORIGIN,"Opening input file %s",fileName);
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");  
  }
  fn = firstEvent; 
  fPhiRandomize = fl;
  fTree = (TTree *)fInputFile->Get("pythia8-Geant4");
  fNevents = fTree->GetEntries();
  // count only events with muons
  // fMuons  = fTree->Draw("id","abs(id)==13","goff");
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
  if (fPhiRandomize){
      Double_t pt  = TMath::Sqrt( px*px+py*py );
      Double_t phi = gRandom->Uniform(0.,2.) * TMath::Pi();
      px = pt*TMath::Sin(phi);
      py = pt*TMath::Cos(phi);
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
