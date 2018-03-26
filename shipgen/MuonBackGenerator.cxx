#include <math.h>
#include "TSystem.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "MuonBackGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt
#include "vetoPoint.h"                
#include "ShipMCTrack.h"                
#include "TMCProcess.h"
#include <algorithm>

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
     TString tmp = gSystem->Getenv("EOSSHIP");
     tmp+=fileName;
     fInputFile  = TFile::Open(tmp); 
  }else{
  fInputFile  = new TFile(fileName);
  }
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file:",fInputFile);
  }
  fn = firstEvent;
  fPhiRandomize = fl;
  fSameSeed = 0;
  fsmearBeam = 0; // default no beam smearing, use SetSmearBeam(sb) if different, sb [cm]
  fTree = (TTree *)fInputFile->Get("pythia8-Geant4");
  if (fTree){
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
  }else{
   id = -1;
   fTree = (TTree *)fInputFile->Get("cbmsim");
   fNevents   = fTree->GetEntries();
   MCTrack = new TClonesArray("ShipMCTrack");
   vetoPoints = new TClonesArray("vetoPoint");
   fTree->SetBranchAddress("MCTrack",&MCTrack);
   fTree->SetBranchAddress("vetoPoint",&vetoPoints);
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
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t mass,e,tof,phi;
  Double_t dx = 0, dy = 0;
  std::vector<int> muList;

  while (fn<fNevents) {
   fTree->GetEntry(fn);
   muList.clear(); 
   fn++;
   if (fn%100000==0)  {fLogger->Info(MESSAGE_ORIGIN,"reading event %i",fn);}
// test if we have a muon, don't look at neutrinos:
   if (abs(int(id))==13) {
        mass = pdgBase->GetParticle(id)->Mass();
        e = TMath::Sqrt( px*px+py*py+pz*pz+mass*mass );
        tof = 0;
        break;}
   if (id==-1){ // use tree as input file
     Bool_t found = false;
     for (int i = 0; i < vetoPoints->GetEntries(); i++) {
         vetoPoint *v = (vetoPoint*)vetoPoints->At(i); 
         if (abs(v->PdgCode())==13){found = true;
           muList.push_back(v->GetTrackID());
            }
     }
     if (!found) {fLogger->Warning(MESSAGE_ORIGIN, "no muon found %i",fn-1);}
     if (found) {break;}
   }
  }
  if (fn>fNevents-1){ 
     fLogger->Info(MESSAGE_ORIGIN,"End of file reached %i",fNevents);
     return kFALSE;
  } 
  if (fSameSeed) {
    Int_t theSeed = fn + fSameSeed * fNevents;
    fLogger->Debug(MESSAGE_ORIGIN, TString::Format("Seed: %d", theSeed));
    gRandom->SetSeed(theSeed);
  }
  if (fPhiRandomize){phi = gRandom->Uniform(0.,2.) * TMath::Pi();}
  if (fsmearBeam > 0) {
     Double_t r = fsmearBeam + 0.8 * gRandom->Gaus();
     Double_t _phi = gRandom->Uniform(0., 2.) * TMath::Pi();
     dx = r * TMath::Cos(_phi);
     dy = r * TMath::Sin(_phi);
  }
  if (id==-1){
     for (unsigned i = 0; i< MCTrack->GetEntries();  i++ ){
       ShipMCTrack* track = (ShipMCTrack*)MCTrack->At(i);
       px = track->GetPx();
       py = track->GetPy();
       pz = track->GetPz();
       if (fPhiRandomize){
        Double_t phi0 = TMath::ATan2(py,px);
        Double_t pt  = track->GetPt();
        px = pt*TMath::Cos(phi+phi0);
        py = pt*TMath::Sin(phi+phi0);
       }
       vx = track->GetStartX()+dx;
       vy = track->GetStartY()+dy;
       vz = track->GetStartZ();
       tof =  track->GetStartT();
       e = track->GetEnergy();
       Bool_t wanttracking = false; // only transport muons
       if(std::find(muList.begin(), muList.end(), i) != muList.end()) {
         wanttracking = true;
       }
       cpg->AddTrack(track->GetPdgCode(),px,py,pz,vx,vy,vz,track->GetMotherId(),wanttracking,e,tof,track->GetWeight(),(TMCProcess)track->GetProcID());
     }
  }else{
    vx += dx/100.;
    vy += dy/100.;
    if (fPhiRandomize){
     Double_t pt  = TMath::Sqrt( px*px+py*py );
     px = pt*TMath::Cos(phi);
     py = pt*TMath::Sin(phi);
    }
    cpg->AddTrack(int(pythiaid),px,py,pz,vx*100.,vy*100.,vz*100.,-1.,false,e,pythiaid,parentid);
    cpg->AddTrack(int(id),px,py,pz,vx*100.,vy*100.,vz*100.,-1.,true,e,tof,w);
  }
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
