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
  return Init(fileName, 0, false);
}
// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName, const int firstEvent, const Bool_t fl = false ) {
  fLogger = FairLogger::GetLogger();
  fLogger->Info(MESSAGE_ORIGIN,"Opening input file %s",fileName);
  if (0 == strncmp("/eos",fileName,4) ) {
     char stupidCpp[100];
     strcpy(stupidCpp,"root://eoslhcb.cern.ch/");
     strcat(stupidCpp,fileName);
     fInputFile  = TFile::Open(stupidCpp); 
  }else{
  fInputFile  = new TFile(fileName);
  }
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");
  }
  fn = firstEvent;
  fPhiRandomize = fl;
  fsmearBeam = 0; // default no beam smearing, use SetSmearBeam(sb) if different, sb [cm]
  fTree = (TTree *)fInputFile->Get("pythia8-Geant4");
  fNevents = fTree->GetEntries();
  // count only events with muons
  // fMuons  = fTree->Draw("id","abs(id)==13","goff");
  fTree->SetBranchAddress("id",&id);                // particle id
  fTree->SetBranchAddress("parentid",&parentid);    // parent id, could be different
  fTree->SetBranchAddress("pythiaid",&pythiaid);    // pythiaid original particle
  fTree->SetBranchAddress("ecut",&ecut);    // energy cut used in simulation
  fTree->SetBranchAddress("w",&w);                  // weight of event
//  check if ntuple has information of momentum at origin
  if (fTree->GetListOfLeaves()->GetSize() < 17){  
   fTree->SetBranchAddress("x",&vx);   // position with respect to startOfTarget at -89.27m
   fTree->SetBranchAddress("y",&vy);
   fTree->SetBranchAddress("z",&vz);
   fTree->SetBranchAddress("px",&px);   // momentum
   fTree->SetBranchAddress("py",&py);
   fTree->SetBranchAddress("pz",&pz);
  }else{
   fTree->SetBranchAddress("ox",&vx);   // position with respect to startOfTarget at -50m
   fTree->SetBranchAddress("oy",&vy);
   fTree->SetBranchAddress("oz",&vz);
   fTree->SetBranchAddress("opx",&px);   // momentum
   fTree->SetBranchAddress("opy",&py);
   fTree->SetBranchAddress("opz",&pz);
  } 
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
      px = pt*TMath::Cos(phi);
      py = pt*TMath::Sin(phi);
  }
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t mass = pdgBase->GetParticle(id)->Mass();
  Double_t    e = TMath::Sqrt( px*px+py*py+pz*pz+mass*mass );
  Double_t tof = 0;
  if (fsmearBeam>0){
    Double_t test = fsmearBeam*fsmearBeam;
    Double_t Rsq  = test + 1.;
    Double_t dx,dy;
    while(Rsq>test){
     dx = gRandom->Uniform(-1.,1.) * fsmearBeam;
     dy = gRandom->Uniform(-1.,1.) * fsmearBeam;
     Rsq = dx*dx+dy*dy;
    }
    vx = vx + dx/100.; 
    vy = vy + dy/100.; 
  }
  cpg->AddTrack(int(pythiaid),px,py,pz,vx*100.,vy*100.,vz*100.,-1.,false,e,pythiaid,parentid);
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
