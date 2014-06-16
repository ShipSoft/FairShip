#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "NtupleGenerator.h"
using std::cout;
using std::endl;
// read events from ntuples produced 

// -----   Default constructor   -------------------------------------------
NtupleGenerator::NtupleGenerator() {}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t NtupleGenerator::Init(const char* fileName) {
  fLogger = FairLogger::GetLogger();
  cout << "Info NtupleGenerator: Opening input file " << fileName << endl;
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");
  }
  fTree = (TTree *)fInputFile->Get("ntuple");
  fNevents = fTree->GetEntries();
  fn = 0;
  fTree->SetBranchAddress("id",&id);                // particle id
  // fTree->SetBranchAddress("parentid",&parentid);    // parent id   
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
    //cout<<"debug ntuple->geant4 "<< fn << " "<< Nmeas <<  " " << procid[Nmeas-1]<< " "<<endl;
    while (fn<fNevents){
     if (fn==fNevents) {fLogger->Fatal(MESSAGE_ORIGIN, "No more input events");}
     fTree->GetEntry(fn);
     fn++;
// test if muon survives:
     if (procid[Nmeas-1]==2) {break;}
    } 
   Int_t i = Nmeas-3;
// first, original muon
    parentid = -1;
    cpg->AddTrack(id,px[0],py[0],pz[0],vx[0]*100.,vy[0]*100.,vz[0]*100.,parentid,false);   
    //cout<<"debug ntuple->geant4 "<< vz[0] << " "<< vz[i] << " "<<endl;
// second, surviving muon
    cpg->AddTrack(id,px[i],py[i],pz[i],vx[i]*100.,vy[i]*100.,vz[i]*100.,0,true);   

  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t NtupleGenerator::GetNevents()
{
 return fNevents;
}


ClassImp(NtupleGenerator)
