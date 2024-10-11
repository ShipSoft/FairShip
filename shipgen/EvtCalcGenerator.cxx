#include <math.h>
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "EvtCalcGenerator.h"
#include "TDatabasePDG.h"
#include "TMath.h"

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
  
  fInputFile = TFile::Open(fileName, "read");
  LOGF(info, "Info EvtCalcGenerator: Opening input file %s", fileName);
  
  fTree = fInputFile->Get("LLP_tree");
  fNevents = fTree->GetEntries();
  fn = firstEvent;

  if (fTree->FindBranch("px_llp") ){fTree->SetBranchAddress("px_llp", &px_llp);}
  if (fTree->FindBranch("py_llp") ){fTree->SetBranchAddress("py_llp", &py_llp);}
  if (fTree->FindBranch("pz_llp") ){fTree->SetBranchAddress("pz_llp", &pz_llp);}
  if (fTree->FindBranch("e_llp") ){fTree->SetBranchAddress("e_llp", &e_llp);}
  if (fTree->FindBranch("pdg_llp") ){fTree->SetBranchAddress("pdg_llp", &pdg_llp);}
  if (fTree->FindBranch("decay_prob") ){fTree->SetBranchAddress("decay_prob", &decay_prob);}
  if (fTree->FindBranch("vx") ){fTree->SetBranchAddress("vx", &vx);}
  if (fTree->FindBranch("vy") ){fTree->SetBranchAddress("vy", &vy);}
  if (fTree->FindBranch("vz") ){fTree->SetBranchAddress("vz", &vz);}

  if (fTree->FindBranch("px_prod1") ){fTree->SetBranchAddress("px_prod1", &px_prod1);}
  if (fTree->FindBranch("py_prod1") ){fTree->SetBranchAddress("py_prod1", &py_prod1);}
  if (fTree->FindBranch("pz_prod1") ){fTree->SetBranchAddress("pz_prod1", &pz_prod1);}
  if (fTree->FindBranch("e_prod1") ){fTree->SetBranchAddress("e_prod1", &e_prod1);}
  if (fTree->FindBranch("pdg_prod1") ){fTree->SetBranchAddress("pdg_prod1", &pdg_prod1);}

  if (fTree->FindBranch("px_prod2") ){fTree->SetBranchAddress("px_prod2", &px_prod2);}
  if (fTree->FindBranch("py_prod2") ){fTree->SetBranchAddress("py_prod2", &py_prod2);}
  if (fTree->FindBranch("pz_prod2") ){fTree->SetBranchAddress("pz_prod2", &pz_prod2);}
  if (fTree->FindBranch("e_prod2") ){fTree->SetBranchAddress("e_prod2", &e_prod2);}
  if (fTree->FindBranch("pdg_prod2") ){fTree->SetBranchAddress("pdg_prod2", &pdg_prod2);}

  if (fTree->FindBranch("px_prod3") ){fTree->SetBranchAddress("px_prod3", &px_prod3);}
  if (fTree->FindBranch("py_prod3") ){fTree->SetBranchAddress("py_prod3", &py_prod3);}
  if (fTree->FindBranch("pz_prod3") ){fTree->SetBranchAddress("pz_prod3", &pz_prod3);}
  if (fTree->FindBranch("e_prod3") ){fTree->SetBranchAddress("e_prod3", &e_prod3);}
  if (fTree->FindBranch("pdg_prod3") ){fTree->SetBranchAddress("pdg_prod3", &pdg_prod3);}

  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
EvtCalcGenerator::~EvtCalcGenerator()
{
 fInputFile->Close();
 fInputFile->Delete();
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t EvtCalcGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  if (fn==fNevents){ 
    LOG(WARNING) << "End of input file. Rewind.";
    fn = 0;
  }

  fTree->GetEntry(fn);
  fn++;
  if (fn %100==0)  LOGF(info, "Info EvtCalcGenerator: event nr %s", fn);

  //Vertex coordinates in the SHiP reference frame, expressed in [cm]
  Double_t space_unit_conv = 100.;            // m to cm 
  Double_t coord_shift     = (zDecayVolume - ztarget)/space_unit_conv; // units m
  Double_t vx_transf = vx * space_unit_conv; // units cm
  Double_t vy_transf = vy * space_unit_conv; // units cm
  Double_t vz_transf = (vz - coord_shift) * space_unit_conv; // units cm

  Double_t c = 2.99792458e+10; // speed of light [cm/s]
  Double_t tof = TMath::Sqrt(vx_transf*vx_transf + vy_transf*vy_transf 
                            + vz_transf*vz_transf)/c;
  
// Mother LLP
  Bool_t wanttracking=false;
  pdg_llp = 999; // Geantino, placeholder
  cpg->AddTrack(pdg_llp, px_llp, py_llp, pz_llp, vx_transf, vy_transf, vz_transf, -1., 
                wanttracking, e_llp, tof, decay_prob);

// Secondaries	
  wanttracking=true;
  cpg->AddTrack(pdg_prod1, px_prod1, py_prod1, pz_prod1, 
                  vx_transf, vy_transf, vz_transf, 0., 
                  wanttracking, e_prod1, tof, decay_prob);
  cpg->AddTrack(pdg_prod2, px_prod2, py_prod2, pz_prod2, 
                  vx_transf, vy_transf, vz_transf, 0., 
                  wanttracking, e_prod2, tof, decay_prob);
  if(pdg_prod3!=-999){
    cpg->AddTrack(pdg_prod3, px_prod3, py_prod3, pz_prod3, 
                    vx_transf, vy_transf, vz_transf, 0., 
                    wanttracking, e_prod3, tof, decay_prob);}
  return kTRUE;
}
