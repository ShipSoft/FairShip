#include <math.h>
#include "TSystem.h"
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
#include "TParticle.h"
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
  LOG(INFO) << "Opening input file"<< fileName;

  iMuon = 0;
  dPart = 0; 
  if (0 == strncmp("/eos",fileName,4) ) {
    TString tmp = gSystem->Getenv("EOSSHIP");
    tmp+=fileName;
    fInputFile  = TFile::Open(tmp); 
    LOG(INFO) << "Open external file on eos:"<<tmp.Data();
  }else{
    fInputFile  = new TFile(fileName);
  }
  if (fInputFile->IsZombie() or !fInputFile) {
     LOG(FATAL) << "Error opening input file";
     return kFALSE; }
  fTree = (TTree *)fInputFile->Get("DIS");
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  fTree->SetBranchAddress("InMuon",&iMuon);    // incoming muon
  fTree->SetBranchAddress("Particles",&dPart);
  return kTRUE;
}
Double_t MuDISGenerator::MeanMaterialBudget(const Double_t *start, const Double_t *end, Double_t *mparam)
{
  //
  // Calculate mean material budget and material properties between
  //    the points "start" and "end".
  //
  // "mparam" - parameters used for the energy and multiple scattering
  //  corrections:
  //
  // mparam[0] - mean density: sum(x_i*rho_i)/sum(x_i) [g/cm3]
  // mparam[1] - equivalent rad length fraction: sum(x_i/X0_i) [adimensional]
  // mparam[2] - mean A: sum(x_i*A_i)/sum(x_i) [adimensional]
  // mparam[3] - mean Z: sum(x_i*Z_i)/sum(x_i) [adimensional]
  // mparam[4] - length: sum(x_i) [cm]
  // mparam[5] - Z/A mean: sum(x_i*Z_i/A_i)/sum(x_i) [adimensional]
  // mparam[6] - number of boundary crosses
  // mparam[7] - maximum density encountered (g/cm^3)
  //
  //  Origin:  Marian Ivanov, Marian.Ivanov@cern.ch
  //
  //  Corrections and improvements by
  //        Andrea Dainese, Andrea.Dainese@lnl.infn.it,
  //        Andrei Gheata,  Andrei.Gheata@cern.ch
  //

  mparam[0]=0; mparam[1]=1; mparam[2] =0; mparam[3] =0;
  mparam[4]=0; mparam[5]=0; mparam[6]=0; mparam[7]=0;
  //
  Double_t bparam[6]; // total parameters
  Double_t lparam[6]; // local parameters

  for (Int_t i=0;i<6;i++) bparam[i]=0;

  if (!gGeoManager) {
    //AliFatalClass("No TGeo\n");
    return 0.;
  }
  //
  Double_t length;
  Double_t dir[3];
  length = TMath::Sqrt((end[0]-start[0])*(end[0]-start[0])+
                       (end[1]-start[1])*(end[1]-start[1])+
                       (end[2]-start[2])*(end[2]-start[2]));
  mparam[4]=length;
  if (length<TGeoShape::Tolerance()) return 0.0;
  Double_t invlen = 1./length;
  dir[0] = (end[0]-start[0])*invlen;
  dir[1] = (end[1]-start[1])*invlen;
  dir[2] = (end[2]-start[2])*invlen;

  // Initialize start point and direction
  TGeoNode *currentnode = 0;
  TGeoNode *startnode = gGeoManager->InitTrack(start, dir);
  if (!startnode) {
    //AliErrorClass(Form("start point out of geometry: x %f, y %f, z %f",
    //		  start[0],start[1],start[2]));
    return 0.0;
  }
  TGeoMaterial *material = startnode->GetVolume()->GetMedium()->GetMaterial();
  lparam[0]   = material->GetDensity();
  if (lparam[0] > mparam[7]) mparam[7]=lparam[0];
  lparam[1]   = material->GetRadLen();
  lparam[2]   = material->GetA();
  lparam[3]   = material->GetZ();
  lparam[4]   = length;
  lparam[5]   = lparam[3]/lparam[2];
  if (material->IsMixture()) {
    TGeoMixture * mixture = (TGeoMixture*)material;
    lparam[5] =0;
    Double_t sum =0;
    for (Int_t iel=0;iel<mixture->GetNelements();iel++){
      sum  += mixture->GetWmixt()[iel];
      lparam[5]+= mixture->GetZmixt()[iel]*mixture->GetWmixt()[iel]/mixture->GetAmixt()[iel];
    }
    lparam[5]/=sum;
  }

  // Locate next boundary within length without computing safety.
  // Propagate either with length (if no boundary found) or just cross boundary
  gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
  Double_t step = 0.0; // Step made
  Double_t snext = gGeoManager->GetStep();
  // If no boundary within proposed length, return current density
  if (!gGeoManager->IsOnBoundary()) {
    mparam[0] = lparam[0];
    mparam[1] = lparam[4]/lparam[1];
    mparam[2] = lparam[2];
    mparam[3] = lparam[3];
    mparam[4] = lparam[4];
    return lparam[0];
  }
  // Try to cross the boundary and see what is next
  Int_t nzero = 0;
  while (length>TGeoShape::Tolerance()) {
    currentnode = gGeoManager->GetCurrentNode();
    if (snext<2.*TGeoShape::Tolerance()) nzero++;
    else nzero = 0;
    if (nzero>3) {
      // This means navigation has problems on one boundary
      // Try to cross by making a small step
      //AliErrorClass("Cannot cross boundary\n");
      mparam[0] = bparam[0]/step;
      mparam[1] = bparam[1];
      mparam[2] = bparam[2]/step;
      mparam[3] = bparam[3]/step;
      mparam[5] = bparam[5]/step;
      mparam[4] = step;
      mparam[0] = 0.;             // if crash of navigation take mean density 0
      mparam[1] = 1000000;        // and infinite rad length
      return bparam[0]/step;
    }
    mparam[6]+=1.;
    step += snext;
    bparam[1]    += snext/lparam[1];
    bparam[2]    += snext*lparam[2];
    bparam[3]    += snext*lparam[3];
    bparam[5]    += snext*lparam[5];
    bparam[0]    += snext*lparam[0];

    if (snext>=length) break;
    if (!currentnode) break;
    length -= snext;
    material = currentnode->GetVolume()->GetMedium()->GetMaterial();
    lparam[0] = material->GetDensity();
    if (lparam[0] > mparam[7]) mparam[7]=lparam[0];
    lparam[1]  = material->GetRadLen();
    lparam[2]  = material->GetA();
    lparam[3]  = material->GetZ();
    lparam[5]   = lparam[3]/lparam[2];
    if (material->IsMixture()) {
      TGeoMixture * mixture = (TGeoMixture*)material;
      lparam[5]=0;
      Double_t sum =0;
      for (Int_t iel=0;iel<mixture->GetNelements();iel++){
        sum+= mixture->GetWmixt()[iel];
        lparam[5]+= mixture->GetZmixt()[iel]*mixture->GetWmixt()[iel]/mixture->GetAmixt()[iel];
      }
      lparam[5]/=sum;
    }
    gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
    snext = gGeoManager->GetStep();
  }
  mparam[0] = bparam[0]/step;
  mparam[1] = bparam[1];
  mparam[2] = bparam[2]/step;
  mparam[3] = bparam[3]/step;
  mparam[5] = bparam[5]/step;
  return bparam[0]/step;
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
    if (fn==fNevents) {LOG(WARNING) << "End of input file. Rewind.";}
    fTree->GetEntry(fn%fNevents);
    fn++;
    if (fn%10000==0) {
      LOG(INFO)  << " heartbeat event-nr "<< fn;
    }
    int nf = dPart->GetEntries();
    LOG(DEBUG) << "*********************************************************";
    LOG(DEBUG) << " " << iMuon->GetEntries()<< " "<< iMuon->AddrAt(0) << " nf "<< nf << " fn=" << fn ; 

    //some start/end positions in z (f.i. emulsion to Tracker 1)
    Double_t start[3]={0.,0.,startZ};
    Double_t end[3]={0.,0.,endZ};

    TParticle* mu = dynamic_cast<TParticle*>(iMuon->AddrAt(0));
    LOG(DEBUG) <<  " in muon " << mu->GetPdgCode()<< endl; 
    Double_t x = mu->Vx();
    Double_t y = mu->Vy();
    Double_t z = mu->Vz();
    Double_t w = mu->GetWeight();
// calculate start/end positions along this muon, and amout of material in between
    Double_t txmu=mu->Px()/mu->Pz();
    Double_t tymu=mu->Py()/mu->Pz();
    start[0]=x-(z-start[2])*txmu;
    start[1]=y-(z-start[2])*tymu;
    end[0] =x-(z-end[2])*txmu;
    end[1] =y-(z-end[2])*tymu;
    LOG(DEBUG) <<  " mu xyz position " << x << ", " << y << ", " << z << endl;
    LOG(DEBUG) <<  " mu pxyz   " << mu->Px() << ", " << mu->Py() << ", " << mu->Pz() ;
    LOG(DEBUG) <<  " mu weight " << w ;
    LOG(DEBUG) <<  "  start position " << start[0] << ", " << start[1] << ", " << start[2] ;
    LOG(DEBUG) <<  " end position " << end[0] << ", " << end[1] << ", " << end[2] ;
    Double_t bparam;
    Double_t mparam[8];
    bparam=MeanMaterialBudget(start, end, mparam);
    //loop over trajectory between start and end to pick an interaction point
    Double_t prob2int = 0.;
    Double_t xmu;
    Double_t ymu;
    Double_t zmu;
    Int_t count=0;
    LOG(DEBUG)  << " Start prob2int while loop, bparam= "              << bparam << ", " << bparam*1.e8 ;
    LOG(DEBUG)  << " What was maximum density, mparam[7]= " << mparam[7] << ", " << mparam[7]*1.e8 ;
    while (prob2int<gRandom->Uniform(0.,1.)) {
      zmu=gRandom->Uniform(start[2],end[2]);
      xmu=x-(z-zmu)*txmu;
      ymu=y-(z-zmu)*tymu;
      //get local material at this point
      TGeoNode *node = gGeoManager->FindNode(xmu,ymu,zmu);
      TGeoMaterial *mat = 0;
      if (node && !gGeoManager->IsOutside()) mat = node->GetVolume()->GetMaterial();
      LOG(DEBUG) << "mat " <<  count << ", " << mat->GetName() << ", " << mat->GetDensity();
      //density relative to Prob largest density along this trajectory, i.e. use rho(Pt)
      prob2int= mat->GetDensity()/mparam[7];
      if (prob2int>1.) LOG(WARNING) << "***WARNING*** MuDISGenerator: prob2int > Maximum density????" << prob2int << " maxrho:" << mparam[7] << " material: " <<  mat->GetName();
      count+=1;
    }
    LOG(DEBUG) << "prob2int " << prob2int << ", " << count ;

    LOG(DEBUG)   << "put position " << xmu << ", " << ymu << ", " << zmu;
    //modify weight, by multiplying with average densiy along track??
    cpg->AddTrack(mu->GetPdgCode(),mu->Px(),mu->Py(),mu->Pz(),xmu,ymu,zmu,-1,false,mu->Energy(),mu->T(),w);
    // in order to have a simulation of possible veto detector hits, let Geant4 follow the muon backward
    // due to dE/dx, as soon as the muon travers thick material, this approximation will become bad. 
    // a proper implementation however would be to have this better integrated in Geant4, follow the muon, call DIS event, continue
    cpg->AddTrack(mu->GetPdgCode(),-(mu->Px()),-(mu->Py()),-(mu->Pz()),xmu,ymu,zmu,0,true,mu->Energy(),mu->T(),w);
// outgoing particles, [did,dpx,dpy,dpz,E], put density along trajectory as weight, g/cm^2
    w=mparam[0]*mparam[4];
    for(int i=0; i<nf; i++)
    	{
         TParticle* Part = dynamic_cast<TParticle*>(dPart->AddrAt(i));
         cpg->AddTrack(Part->GetPdgCode(),Part->Px(),Part->Py(),Part->Pz(),xmu,ymu,zmu,0,true,Part->Energy(),mu->T(),w);
       }
  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t MuDISGenerator::GetNevents()
{
 return fNevents;
}

ClassImp(MuDISGenerator)
