#include <math.h>
#include "TROOT.h"
#include "TMath.h"
#include "TFile.h"
#include "TRandom.h"
#include "FairPrimaryGenerator.h"
#include "MuDISGenerator.h"
#include "TGeoVolume.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoEltu.h"
#include "TVectorD.h"
#include "TGeoCompositeShape.h"

using std::cout;
using std::endl;
// read events from ntuples produced with MuDIS
// http://MuDIS.hepforge.org/manuals/MuDIS_PhysicsAndUserManual_20130615.pdf
// MuDIS momentum GeV
// Vertex in SI units, assume this means m
// important to read back number of events to give to FairRoot

// -----   Default constructor   -------------------------------------------
MuDISGenerator::MuDISGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t MuDISGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t MuDISGenerator::Init(const char* fileName, const int firstEvent) {
  fLogger = FairLogger::GetLogger();
  fLogger->Info(MESSAGE_ORIGIN,"Opening input file %s",fileName);

  iMuon = 0;
  dPart = 0; 
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");
  }
  fTree = (TTree *)fInputFile->Get("DIS");
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  fTree->SetBranchAddress("InMuon",&iMuon);    // incoming muon
  fTree->SetBranchAddress("Particles",&dPart);
  // cout << "muon DIS Generator number of events "<< fNevents << endl; 
  return kTRUE;
}

// -----   Destructor   ----------------------------------------------------
MuDISGenerator::~MuDISGenerator()
{
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -----   Passing the event   ---------------------------------------------
Bool_t MuDISGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    if (fn==fNevents) {fLogger->Warning(MESSAGE_ORIGIN, "End of input file. Rewind.");}
    fTree->GetEntry(fn%fNevents);
    fn++;
    if (fn%100==0) {
      cout << "Info MuDISGenerator: neutrino event-nr "<< fn << endl;
    }
    int nf = dPart->GetEntries();
    // cout << "muon DIS Generator debug " << iMuon->GetEntries()<< " "<< iMuon->AddrAt(0) << " nf "<< nf << endl; 

// incoming muon  array('d',[pid,px,py,pz,x,y,z,w])
    TVectorD* mu = dynamic_cast<TVectorD*>(iMuon->AddrAt(0));
    // cout << "muon DIS Generator in muon " << int(mu[0][0])<< endl; 
    cpg->AddTrack(int(mu[0][0]),mu[0][1],mu[0][2],mu[0][3],
        mu[0][5],mu[0][6],mu[0][7],-1,false,mu[0][4],0.,mu[0][8]);
// outgoing particles, [did,dpx,dpy,dpz,E]
    for(int i=0; i<nf; i++)
    	{
         TVectorD* Part = dynamic_cast<TVectorD*>(dPart->AddrAt(i));
         //cout << "muon DIS Generator out part " << int(Part[0][0]) << endl; 
         //cout << "muon DIS Generator out part mom " << Part[0][1]<<" " << Part[0][2] <<" " << Part[0][3] << " " << Part[0][4] << endl; 
         //cout << "muon DIS Generator out part pos " << mu[0][5]<<" " << mu[0][6] <<" " << mu[0][7] << endl; 
         //cout << "muon DIS Generator out part w " << mu[0][8] << endl; 
         cpg->AddTrack(int(Part[0][0]),Part[0][1],Part[0][2],Part[0][3],mu[0][5],mu[0][6],mu[0][7],0,true,Part[0][4],0.,mu[0][8]);
         //cout << "muon DIS part added "<<endl;
       }
  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t MuDISGenerator::GetNevents()
{
 return fNevents;
}

ClassImp(MuDISGenerator)
