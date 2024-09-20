#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "LLPGenerator.h"
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
LLPGenerator::LLPGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t LLPGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t LLPGenerator::Init(const char* fileName, const int firstEvent) {
  
  cout << "Info LLPGenerator: Opening input file " << fileName << endl;
  fLogger = FairLogger::GetLogger();
	if (0 == strncmp("/eos", fileName,4)){
		TString tmp = gSystem->Getenv("EOSSHIP");
		tmp+=fileName;
		fInputFile  = TFile::Open(tmp); 
		fLogger->Info(MESSAGE_ORIGIN,"Info LLPGenerator: Opening input file on eos %s",tmp.Data());
	}else{
		fInputFile = new TFile(fileName);
		fLogger->Info(MESSAGE_ORIGIN,"Info LLPGenerator: Opening input file %s",fileName);}
	
	if (fInputFile->IsZombie() or !fInputFile){
     		fLogger->Fatal(MESSAGE_ORIGIN, "Info LLPGenerator: Error opening input file");
	return kFALSE;}
  
  fTree = (TTree *)fInputFile->Get("ntuple");
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  // if (fTree->FindBranch("parentid") ){ fTree->SetBranchAddress("parentid",&parentid);}    // parent id
  
  fTree->SetBranchAddress("parentid",&parentid)
  fTree->SetBranchAddress("px", &px);   // incoming LLP spatial momentum
  fTree->SetBranchAddress("py", &py);
  fTree->SetBranchAddress("pz", &pz);
  fTree->SetBranchAddress("energy", &energy);
  fTree->SetBranchAddress("weight",&weight); // event weight
  fTree->SetBranchAddress("E_2ry",&E_2ry);	 // energy 2ry
  fTree->SetBranchAddress("vx",&vx);         // vertex position
  fTree->SetBranchAddress("vy",&vy);
  fTree->SetBranchAddress("vz",&vz);
  fTree->SetBranchAddress("px_2ry",&px_2ry); // spatial momentum 2ry
	fTree->SetBranchAddress("py_2ry",&py_2ry);
	fTree->SetBranchAddress("pz_2ry",&pz_2ry);
  fTree->SetBranchAddress("energy_2ry",&energy_2ry);
  fTree->SetBranchAddress("pdg_2ry",&pdg_2ry);	// pdg code 2ry
	fTree->SetBranchAddress("n_2ry",&n_2ry);	    // nr 2ry
  
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
LLPGenerator::~LLPGenerator()
{
 // cout << "destroy Ntuple" << endl;
 fInputFile->Close();
 fInputFile->Delete();
 delete fInputFile;
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t LLPGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{

  //Vertex coordinates in the SHiP reference frame, expressed in [cm]
  Double_t space_unit_conv = 100.;            // m to cm 
  Double_t coord_shift     = (zDecayVolume - ztarget)/space_unit_conv; // units m
  Double_t vx_transf = vx * space_unit_conv; // units cm
  Double_t vy_transf = vy * space_unit_conv; // units cm
	Double_t vz_transf = (vz + coord_shift) * space_unit_conv; // units cm

  if (fn==fNevents)  fLogger->Warning(MESSAGE_ORIGIN, "End of input file. Rewind.");

  fTree->GetEntry(fn);
  fn++;
  if (fn %100==0)  cout << "Info LLPGenerator: event nr "<< fn << endl;
  int nPart = n_2ry->GetEntries();

  Double_t c   = 2.99792458e+6;
	Double_t tof = TMath::Sqrt(vx_transf*vx_transf + vy_transf*vy_transf 
                             + vz_transf*vz_transf)/c;

// Mother LLP
  Bool_t wanttracking=false;
  cpg->AddTrack(parentid, px, py, pz, vx_transf, vy_transf, vz_transf, -1., 
                wanttracking, energy, tof, weight);

// Secondaries	
  wanttracking=true;
  for(int ipart=0; ipart<nPart; ++ipart){
    if (fileName && *fileName){im+=1;};
		cpg->AddTrack(pdg_2ry[ipart], px_2ry[ipart], py_2ry[ipart], pz_2ry[ipart], 
                  vx_transf, vy_transf, vz_transf, ipart, wanttracking, energy_2ry[i], 
                  tof, weight);
	}
  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t LLPGenerator::GetNevents()
{
 return fNevents;
}
