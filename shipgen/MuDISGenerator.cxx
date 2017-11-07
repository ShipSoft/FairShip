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
  if (0 == strncmp("/eos",fileName,4) ) {
    TString tmp = gSystem->Getenv("EOSSHIP");
    tmp+=fileName;
    fInputFile  = TFile::Open(tmp); 
    fLogger->Info(MESSAGE_ORIGIN,"Open external file on eos: %s",tmp.Data());
  }else{
    fInputFile  = new TFile(fileName);
  }
  if (fInputFile->IsZombie() or !fInputFile) {
     fLogger->Fatal(MESSAGE_ORIGIN, "Error opening input file");
     return kFALSE; }
  fTree = (TTree *)fInputFile->Get("DIS");
  fNevents = fTree->GetEntries();
  fn = firstEvent;
  fTree->SetBranchAddress("InMuon",&iMuon);    // incoming muon
  fTree->SetBranchAddress("Particles",&dPart);
  // cout << "muon DIS Generator number of events "<< fNevents << endl; 
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
    if (fn==fNevents) {fLogger->Warning(MESSAGE_ORIGIN, "End of input file. Rewind.");}
    fTree->GetEntry(fn%fNevents);
    fn++;
    if (fn%100==0) {
      cout << "Info MuDISGenerator: MuDIS event-nr "<< fn << endl;
    }
    int nf = dPart->GetEntries();
    //cout << "*********************************************************" << endl;
    //cout << "muon DIS Generator debug " << iMuon->GetEntries()<< " "<< iMuon->AddrAt(0) << " nf "<< nf << " fn=" << fn <<endl; 

    //some start/end positions in z (f.i. emulsion to Tracker 1)
    Double_t start[3]={0.,0.,startZ};
    Double_t end[3]={0.,0.,endZ};

// incoming muon  array('d',[pid,px,py,pz,E,x,y,z,w])
    TVectorD* mu = dynamic_cast<TVectorD*>(iMuon->AddrAt(0));
    //cout << "muon DIS Generator in muon " << int(mu[0][0])<< endl; 
    Double_t x = mu[0][5]*100.; // come in m -> cm
    Double_t y = mu[0][6]*100.; // come in m -> cm
    Double_t z = mu[0][7]*100.; // come in m -> cm
    Double_t w = mu[0][8];
// calculate start/end positions along this muon, and amout of material in between
    Double_t txmu=mu[0][1]/mu[0][3];
    Double_t tymu=mu[0][2]/mu[0][3];
    start[0]=x-(z-start[2])*txmu;
    start[1]=y-(z-start[2])*tymu;
    end[0]=x-(z-end[2])*txmu;
    end[1]=y-(z-end[2])*tymu;
    //cout << "MuDIS: mu xyz position " << x << ", " << y << ", " << z << endl;
    //cout << "MuDIS: mu pxyz position " << mu[0][1] << ", " << mu[0][2] << ", " << mu[0][3] << endl;
    //cout << "MuDIS: mu weight " << w << endl;
    //cout << "MuDIS: start position " << start[0] << ", " << start[1] << ", " << start[2] << endl;
    //cout << "MuDIS: end position " << end[0] << ", " << end[1] << ", " << end[2] << endl;
    Double_t bparam;
    Double_t mparam[8];
    bparam=MeanMaterialBudget(start, end, mparam);
    //loop over trajectory between start and end to pick an interaction point
    Double_t prob2int = 0.;
    Double_t xmu;
    Double_t ymu;
    Double_t zmu;
    Int_t count=0;
    //cout << "Info MuDISGenerator Start prob2int while loop, bparam= " << bparam << ", " << bparam*1.e8 <<endl;
    //cout << "Info MuDISGenerator What was maximum density, mparam[7]= " << mparam[7] << ", " << mparam[7]*1.e8 <<endl;
    while (prob2int<gRandom->Uniform(0.,1.)) {
      zmu=gRandom->Uniform(start[2],end[2]);
      xmu=x-(z-zmu)*txmu;
      ymu=y-(z-zmu)*tymu;
      //get local material at this point
      TGeoNode *node = gGeoManager->FindNode(xmu,ymu,zmu);
      TGeoMaterial *mat = 0;
      if (node && !gGeoManager->IsOutside()) mat = node->GetVolume()->GetMaterial();
      //cout << "Info MuDISGenerator: mat " <<  count << ", " << mat->GetName() << ", " << mat->GetDensity() << endl;
      //density relative to Prob largest density along this trajectory, i.e. use rho(Pt)
      prob2int= mat->GetDensity()/mparam[7];
      if (prob2int>1.) cout << "***WARNING*** MuDISGenerator: prob2int > Maximum density????" << prob2int << " maxrho:" << mparam[7] << " material: " <<  mat->GetName() << endl;
      count+=1;
    }
    //cout << "Info MuDISGenerator: prob2int " << prob2int << ", " << count << endl;

    //cout << "MuDIS: put position " << xmu << ", " << ymu << ", " << zmu << endl;
    //modify weight, by multiplying with average densiy along track??
    cpg->AddTrack(int(mu[0][0]),mu[0][1],mu[0][2],mu[0][3],xmu,ymu,zmu,-1,false,mu[0][4],0.,w);
    // in order to have a simulation of possible veto detector hits, let Geant4 follow the muon backward
    // due to dE/dx, as soon as the muon travers thick material, this approximation will become bad. 
    // a proper implementation however would be to have this better integrated in Geant4, follow the muon, call DIS event, continue
    cpg->AddTrack(int(mu[0][0]),-mu[0][1],-mu[0][2],-mu[0][3],xmu,ymu,zmu,0,true,mu[0][4],0.,w);
// outgoing particles, [did,dpx,dpy,dpz,E], put density along trajectory as weight, g/cm^2
    w=mparam[0]*mparam[4];
    for(int i=0; i<nf; i++)
    	{
         TVectorD* Part = dynamic_cast<TVectorD*>(dPart->AddrAt(i));
         //cout << "muon DIS Generator out part " << int(Part[0][0]) << endl; 
         //cout << "muon DIS Generator out part mom " << Part[0][1]<<" " << Part[0][2] <<" " << Part[0][3] << " " << Part[0][4] << endl; 
         //cout << "muon DIS Generator out part pos " << mu[0][5]<<" " << mu[0][6] <<" " << mu[0][7] << endl; 
         //cout << "muon DIS Generator out part w " << mu[0][8] << endl; 
         cpg->AddTrack(int(Part[0][0]),Part[0][1],Part[0][2],Part[0][3],xmu,ymu,zmu,0,true,Part[0][4],0.,w);
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
