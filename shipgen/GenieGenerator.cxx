#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "GenieGenerator.h"
using std::cout;
using std::endl;
// read events from ntuples produced with GENIE
// http://genie.hepforge.org/manuals/GENIE_PhysicsAndUserManual_20130615.pdf 
// Genie momentum GeV
// Vertex in SI units, assume this means m
// important to read back number of events to give to FairRoot

// -----   Default constructor   -------------------------------------------
GenieGenerator::GenieGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t GenieGenerator::Init(const char* fileName) {
 Init(fileName, 0); 
}
// -----   Default constructor   -------------------------------------------
Bool_t GenieGenerator::Init(const char* fileName, const int firstEvent) {
  fLogger = FairLogger::GetLogger();
  fLogger->Info(MESSAGE_ORIGIN,"Opening input file %s",fileName);
  fInputFile  = new TFile(fileName);
  if (fInputFile->IsZombie()) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Error opening the Signal file");
  }
  fTree = (TTree *)fInputFile->Get("gst");
  fNevents = fTree->GetEntries();
  fn = firstEvent; 
  fTree->SetBranchAddress("Ev",&pxl);    // incoming neutrino energy
  fTree->SetBranchAddress("pxv",&pxv);     
  fTree->SetBranchAddress("pyv",&pyv);     
  fTree->SetBranchAddress("pzv",&pzv);     
  fTree->SetBranchAddress("neu",&neu);    // incoming neutrino PDG code
  fTree->SetBranchAddress("vtxx",&vtxx);  // vertex  in SI units   
  fTree->SetBranchAddress("vtxy",&vtxy);    
  fTree->SetBranchAddress("vtxz",&vtxz);   
  fTree->SetBranchAddress("vtxt",&vtxt);   
  fTree->SetBranchAddress("El",&El);      // outgoing lepton momentum
  fTree->SetBranchAddress("pxl",&pxl);    
  fTree->SetBranchAddress("pyl",&pyl);
  fTree->SetBranchAddress("pzl",&pzl);
  fTree->SetBranchAddress("pxf",&pxf);   // outgoing hadronic momenta
  fTree->SetBranchAddress("pyf",&pyf);
  fTree->SetBranchAddress("pzf",&pzf);
  fTree->SetBranchAddress("nf",&nf);     // nr of outgoing hadrons
  fTree->SetBranchAddress("pdgf",&pdgf);     // pdg code of hadron

  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
GenieGenerator::~GenieGenerator() 
{
 fInputFile->Close(); 
 fInputFile->Delete(); 
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t GenieGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    if (fn==fNevents) {fLogger->Fatal(MESSAGE_ORIGIN, "No more input events");}
    fTree->GetEntry(fn);
    fn++;
// first, incoming neutrino
    cpg->AddTrack(neu,pxv,pyv,pzv,vtxx,vtxy,vtxz,-1,false);   
    //cout << "Info GenieGenerator: neutrino " << neu << " "<<  pzv << " nf "<< nf << endl;

// second, outgoing lepton
    cpg->AddTrack(copysign(fabs(neu)-1,neu),pxl,pyl,pzl,vtxx*100.,vtxy*100.,vtxz*100.,0,true); 
// last, all others
    for(int i=0; i<nf; i++)
	{
         cpg->AddTrack(pdgf[i],pxf[i],pyf[i],pzf[i],vtxx*100.,vtxy*100.,vtxz*100.,0,true);    
         // cout << "f " << pdgf[i] << " pz "<< pzf[i] << endl;
       }

  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t GenieGenerator::GetNevents()
{
 return fNevents;
}


ClassImp(GenieGenerator)
