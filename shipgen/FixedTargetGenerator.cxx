#include <math.h>
#include <array>
#include "TROOT.h"
#include "FairPrimaryGenerator.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include <TGeoManager.h>
#include "TGeoBBox.h"
#include "Pythia8/Pythia.h"
#include "TMath.h"
#include "FixedTargetGenerator.h"
#include "HNLPythia8Generator.h"

const Double_t cm = 10.; // pythia units are mm
const Double_t c_light = 2.99792458e+10; // speed of light in cm/sec (c_light   = 2.99792458e+8 * m/s)
const Double_t mbarn = 1E-3*1E-24*TMath::Na(); // cm^2 * Avogadro

using namespace Pythia8;

// -----   Default constructor   -------------------------------------------
FixedTargetGenerator::FixedTargetGenerator() 
{
  fUseRandom1 = kFALSE; 
  fUseRandom3 = kTRUE;
  fSeed = 0;
  fMom        = 400;  // proton
  fLogger = FairLogger::GetLogger();
  targetName = ""; 
  xOff=0; yOff=0;
  tauOnly = false;
  JpsiMainly = false;
  G4only = false;
  maxCrossSection = 0.;
  EMax = 0;
  fBoost = 1.;
  fPythiaN =  new Pythia8::Pythia();
  fPythiaP =  new Pythia8::Pythia();
}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t FixedTargetGenerator::Init() 
{
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();
  fPythiaP->settings.mode("Beams:idB",  2212);
  fPythiaN->settings.mode("Beams:idB",  2112);
  std::array<Pythia8::Pythia*,2> plist = {fPythiaP,fPythiaN};
  std::vector<int> s = { 211,321,130,310,3122,3112,3312 };
  std::vector<int> r = { 221, 223,   113, 331, 333};
  std::vector<int> c = { 7, 7, 5, 6, 9}; // decay channel mumu
  for(const auto& fPythia : plist) {
   fPythia->setRndmEnginePtr(fRandomEngine);
   fPythia->settings.mode("Random:seed",fSeed);

   fPythia->settings.mode("Beams:idA",  2212);
   fPythia->settings.mode("Beams:frameType",  2);
   fPythia->settings.parm("Beams:eA",fMom);
   fPythia->settings.parm("Beams:eB",0.);

   fPythia->readString("Next:numberCount = 100000");
   fPythia->readString("SoftQCD:inelastic = on");
   fPythia->readString("PhotonCollision:gmgm2mumu = on");
   fPythia->readString("PromptPhoton:all = on");
   fPythia->readString("WeakBosonExchange:all = on");
// http://home.thep.lu.se/~torbjorn/pythia81html/ParticleDecays.html
   if (tauOnly){
    fPythia->readString("431:new  D_s+  D_s-  1   3   0    1.96849    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0");
    fPythia->readString("431:addChannel = 1   0.0640000    0      -15       16");
   }
   if (JpsiMainly){
    fPythia->readString("443:new  J/psi  J/psi  4   0   0    3.09692    0.00009    3.09602    3.09782  0.   1   1   0   1   0");
    fPythia->readString("443:addChannel = 1   0.1    0      -13       13");
   }
  
// make pions/kaons/lambda stable  
   for (unsigned int i=0; i<s.size(); ++i) {
    string particle = std::to_string(s[i])+":mayDecay = false";
    fPythia->readString(particle);
  }
// boost branching fraction of rare di-muon decays
//                       eta  omega rho0  eta' phi   
   if (fBoost != 1.){
    fLogger->Info(MESSAGE_ORIGIN,"Rescale BRs of dimuon decays in Pythia: %f",fBoost);
    for (unsigned int i=0; i<r.size(); ++i) {  
     Pythia8::ParticleDataEntry* V = fPythia->particleData.particleDataEntryPtr(r[i]);
     Pythia8::DecayChannel ch = V->channel(c[i]);
     if (TMath::Abs(ch.product(0))!=13 || TMath::Abs(ch.product(1))!=13){
      fLogger->Info(MESSAGE_ORIGIN,"this is not the right decay channel: %i %i",r[i],c[i]);
     }else{
      ch.rescaleBR(fBoost);
     }
    }
   }
   fPythia->init();
  }
  if (targetName!=""){
   fMaterialInvestigator = new GenieGenerator();
   TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
   nav->cd(targetName);
   TGeoNode* target = nav->GetCurrentNode(); 
   TObjArray* nodes =  target->GetVolume()->GetNodes();
   TGeoNode* first = (TGeoNode*)nodes->At(0);
   Int_t ilast = nodes->GetSize()-5; // assumes that the last 5 nodes are for the shielding around the target.
   TGeoNode* last  = (TGeoNode*)nodes->At(ilast);
   nav->cd(targetName+"/"+first->GetName()); 
   TGeoBBox* sha = (TGeoBBox*)first->GetVolume()->GetShape();
   Double_t dz   = sha->GetDZ();
   Double_t origin[3] = {0,0,-dz};
   Double_t master[3] = {0,0,0};
   nav->LocalToMaster(origin,master);
   startZ =  master[2];
   nav->cd(targetName+"/"+last->GetName()); 
   sha = (TGeoBBox*)first->GetVolume()->GetShape();
   dz   = sha->GetDZ();
   origin[2] = +dz;
   nav->LocalToMaster(origin,master);
   endZ =  master[2];
   start[0]=xOff;
   start[1]=yOff;
   start[2]=startZ;
   end[0]=xOff;
   end[1]=yOff;
   end[2]=endZ;
//find maximum interaction length
   bparam = fMaterialInvestigator->MeanMaterialBudget(start, end, mparam);
   maxCrossSection =  mparam[9];
  }
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
FixedTargetGenerator::~FixedTargetGenerator() 
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t FixedTargetGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
  Double_t zinter=0;
  Double_t ZoverA = 1.;
  if (targetName!=""){
// calculate primary proton interaction point:
// loop over trajectory between start and end to pick an interaction point, copied from GenieGenerator and adapted to hadrons
   Double_t prob2int = -1.;
   Double_t rndm = 0.;
   Double_t sigma;
   Int_t count=0;
   while (prob2int<rndm) {
 //place x,y,z uniform along path
      zinter = gRandom->Uniform(start[2],end[2]);
      Double_t point[3]={xOff,yOff,zinter};
      bparam = fMaterialInvestigator->MeanMaterialBudget(start, point, mparam);
      Double_t interLength = mparam[8]; 
      TGeoNode *node = gGeoManager->FindNode(point[0],point[1],point[2]);
      TGeoMaterial *mat = 0;
      if (node && !gGeoManager->IsOutside()) {
         mat = node->GetVolume()->GetMaterial();
         Double_t n = mat->GetDensity()/mat->GetA();
         ZoverA =  mat->GetZ() / mat->GetA();
         sigma = 1./(n*mat->GetIntLen())/mbarn;
         prob2int = TMath::Exp(-interLength)*sigma/maxCrossSection;
      }else{
         prob2int=0.;
      }
      // cout<< "positioning "<<zinter<<" "<<interLength<<" "<<start[2]<<" "<<end[2]<<" "<<prob2int<<" "<<maxCrossSection<<endl;
      rndm = gRandom->Uniform(0.,1.); 
      count+=1;
   }
  zinter = zinter*cm;
  }
  if (G4only){
   cpg->AddTrack(2212,0.,0.,fMom,xOff/cm,yOff/cm,zinter/cm,-1,true,-1.,0.,1.);  
  }else{
  Pythia8::Pythia* fPythia;
  if (gRandom->Uniform(0.,1.) < ZoverA){
    fPythia = fPythiaP;
  }else{
    fPythia = fPythiaN;
  }
  fPythia->next();

  for(Int_t ii=0; ii<fPythia->event.size(); ii++){
     Double_t  e = fPythia->event[ii].e();
     Double_t  m = fPythia->event[ii].m();
     Double_t pz = fPythia->event[ii].pz();
     Int_t id = fPythia->event[ii].id(); 
     Bool_t wanttracking=true;
     if (e-m<EMax || !fPythia->event[ii].isFinal() || pz<0) {wanttracking=false;}
     Double_t z  = fPythia->event[ii].zProd()+zinter;
     Double_t x  = fPythia->event[ii].xProd()+xOff;
     Double_t y  = fPythia->event[ii].yProd()+yOff;
     Double_t tof = fPythia->event[ii].tProd();
     Double_t px = fPythia->event[ii].px();  
     Double_t py = fPythia->event[ii].py();  
     Int_t im = fPythia->event[ii].mother1();
     if (ii==0){im = -1;}
     cpg->AddTrack(id,px,py,pz,x/cm,y/cm,z/cm,im,wanttracking,e,tof,1.);
    }    
  }
  return kTRUE;
}
// -------------------------------------------------------------------------

ClassImp(FixedTargetGenerator)
