#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "EvtCalcGenerator.h"
#include "TDatabasePDG.h"
#include "TMath.h"
#include "TGeoVolume.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoEltu.h"
#include "TVectorD.h"
#include "TGeoCompositeShape.h"

using std::cout;
using std::endl;
// read events from ntuples produced

// -----   Default constructor   -------------------------------------------
EvtCalcGenerator::EvtCalcGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t EvtCalcGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t EvtCalcGenerator::Init(const char* fileName, const int firstEvent) {
  
  cout << "Info EvtCalcGenerator: Opening input file " << fileName << endl;
  if (0 == strncmp("/eos",fileName,4) ) {
    TString tmp = gSystem->Getenv("EOSSHIP");
    tmp+=fileName;
    fInputFile  = TFile::Open(tmp);
    LOGF(info, "Info EvtCalcGenerator: Opening input file on eos %s",tmp.Data());
  }else{
    fInputFile  = new TFile(fileName);
    LOGF(info, "Info EvtCalcGenerator: Opening input file %s", fileName);
  }
  if (fInputFile->IsZombie() or !fInputFile) {
      LOG(FATAL) << "Info EvtCalcGenerator: Error opening input file";
      return kFALSE; }
  
  fTree = (TTree *)fInputFile->Get("LLP_tree");
  fNevents = fTree->GetEntries();
  fn = firstEvent;

  fTree->SetBranchAddress("px_llp", &px_llp);
  fTree->SetBranchAddress("py_llp", &py_llp);
  fTree->SetBranchAddress("pz_llp", &pz_llp);
  fTree->SetBranchAddress("e_llp", &e_llp);
  fTree->SetBranchAddress("pdg_lpp", &pdg_lpp);
  fTree->SetBranchAddress("decay_prob", &decay_prob);
  fTree->SetBranchAddress("vx", &vx);
  fTree->SetBranchAddress("vy", &vy);
  fTree->SetBranchAddress("vz", &vz);

  fTree->SetBranchAddress("px_prod1", &px_prod1);
  fTree->SetBranchAddress("py_prod1", &py_prod1);
  fTree->SetBranchAddress("pz_prod1", &pz_prod1);
  fTree->SetBranchAddress("e_prod1", &e_prod1);
  fTree->SetBranchAddress("pdg_prod1", &pdg_prod1);

  fTree->SetBranchAddress("px_prod2", &px_prod2);
  fTree->SetBranchAddress("py_prod2", &py_prod2);
  fTree->SetBranchAddress("pz_prod2", &pz_prod2);
  fTree->SetBranchAddress("e_prod2", &e_prod2);
  fTree->SetBranchAddress("pdg_prod2", &pdg_prod2);

  fTree->SetBranchAddress("px_prod3", &px_prod3);
  fTree->SetBranchAddress("py_prod3", &py_prod3);
  fTree->SetBranchAddress("pz_prod3", &pz_prod3);
  fTree->SetBranchAddress("e_prod3", &e_prod3);
  fTree->SetBranchAddress("pdg_prod3", &pdg_prod3);

  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
EvtCalcGenerator::~EvtCalcGenerator()
{
 // cout << "destroy Ntuple" << endl;
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t EvtCalcGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{

  //Vertex coordinates in the SHiP reference frame, expressed in [cm]
  Double_t space_unit_conv = 100.;            // m to cm 
  Double_t coord_shift     = (zDecayVolume - ztarget)/space_unit_conv; // units m
  Double_t vx_transf = vx * space_unit_conv; // units cm
  Double_t vy_transf = vy * space_unit_conv; // units cm
	Double_t vz_transf = (vz + coord_shift) * space_unit_conv; // units cm

  if (fn==fNevents){ LOG(WARNING) << "End of input file. Rewind."; }

  fTree->GetEntry(fn);
  fn++;
  if (fn %100==0)  cout << "Info EvtCalcGenerator: event nr "<< fn << endl;

  Double_t c   = 2.99792458e+6;
	Double_t tof = TMath::Sqrt(vx_transf*vx_transf + vy_transf*vy_transf 
                            + vz_transf*vz_transf)/c;

// Mother LLP
  Bool_t wanttracking=false;
  cpg->AddTrack(pdg_lpp, px_llp, py_llp, pz_llp, vx_transf, vy_transf, vz_transf, -1., 
                wanttracking, e_llp, tof, decay_prob);

// Secondaries	
  wanttracking=true;
  
  cpg->AddTrack(pdg_prod1, px_prod1, py_prod1, pz_prod1, 
                  vx_transf, vy_transf, vz_transf, 0., 
                  wanttracking, e_prod1, tof, decay_prob);
  cpg->AddTrack(pdg_prod2, px_prod2, py_prod2, pz_prod2, 
                  vx_transf, vy_transf, vz_transf, 1., 
                  wanttracking, e_prod2, tof, decay_prob);
  if(pdg_prod3!=-999){
    cpg->AddTrack(pdg_prod3, px_prod3, py_prod3, pz_prod3, 
                    vx_transf, vy_transf, vz_transf, 2., 
                    wanttracking, e_prod3, tof, decay_prob);}
  return kTRUE;
}
