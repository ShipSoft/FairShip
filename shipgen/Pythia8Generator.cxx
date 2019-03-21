#include <math.h>
#include "TSystem.h"
#include "TROOT.h"
#include "FairPrimaryGenerator.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include <TGeoManager.h>
#include "TGeoBBox.h"
#include "TMath.h"
#include "Pythia8Generator.h"
#include "HNLPythia8Generator.h"
const Double_t cm = 10.; // pythia units are mm
const Double_t c_light = 2.99792458e+10; // speed of light in cm/sec (c_light   = 2.99792458e+8 * m/s)
Int_t counter = 0;
const Double_t mbarn = 1E-3*1E-24*TMath::Na(); // cm^2 * Avogadro

using namespace Pythia8;

// -----   Default constructor   -------------------------------------------
Pythia8Generator::Pythia8Generator() 
{
  fUseRandom1 = kFALSE; 
  fUseRandom3 = kTRUE;
  fId         = 2212; // proton
  fMom        = 400;  // proton
  fFDs        = 7.7/10.4;    // correction for Pythia6 to match measured Ds production
  fextFile    = "";
  fInputFile  = NULL;
  fLogger = FairLogger::GetLogger();
  targetName = ""; 
  xOff=0; yOff=0;
  fPythia =  new Pythia8::Pythia();
}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t Pythia8Generator::Init() 
{
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();
  if (fextFile && *fextFile) {
    if (0 == strncmp("/eos",fextFile,4) ) {
     TString tmp = gSystem->Getenv("EOSSHIP");
     tmp+=fextFile;
     fInputFile  = TFile::Open(tmp); 
     fLogger->Info(MESSAGE_ORIGIN,"Open external file with charm or beauty hadrons on eos: %s",tmp.Data());
     if (!fInputFile) {
      fLogger->Fatal(MESSAGE_ORIGIN, "Error opening input file. You may have forgotten to provide a krb5 token. Try kinit username@lxplus.cern.ch");
      return kFALSE; }
    }else{
      fLogger->Info(MESSAGE_ORIGIN,"Open external file with charm or beauty hadrons: %s",fextFile);
      fInputFile  = new TFile(fextFile);
      if (!fInputFile) {
       fLogger->Fatal(MESSAGE_ORIGIN, "Error opening input file");
     return kFALSE; }
    }
    if (fInputFile->IsZombie()) {
     fLogger->Fatal(MESSAGE_ORIGIN, "File is corrupted");
     return kFALSE; }
     fTree = (TTree *)fInputFile->Get("pythia6");
     fNevents = fTree->GetEntries();
     fn = firstEvent;
     fTree->SetBranchAddress("id",&hid);                // particle id
     fTree->SetBranchAddress("px",&hpx);   // momentum
     fTree->SetBranchAddress("py",&hpy);
     fTree->SetBranchAddress("pz",&hpz);
     fTree->SetBranchAddress("E",&hE);     
     fTree->SetBranchAddress("M",&hM);     
     fTree->SetBranchAddress("mid",&mid);   // mother
     fTree->SetBranchAddress("mpx",&mpx);   // momentum
     fTree->SetBranchAddress("mpy",&mpy);
     fTree->SetBranchAddress("mpz",&mpz);
     fTree->SetBranchAddress("mE",&mE);
     if (fTree->GetBranch("k")){
      fTree->SetBranchAddress("k",&ck);
      if (fTree->GetBranch("a0")){
       for(Int_t i=0; i<16; i++){
        TString na = "a";na+=i;
        fTree->SetBranchAddress(na,&(ancestors[i]));
        TString ns = "s";ns+=i;
        fTree->SetBranchAddress(ns,&(subprocCodes[i]));
       }
      }
     }else{
      ck[0]=1;subprocCodes[0]=88;ancestors[0]=2212;
     }
     fPythia->readString("ProcessLevel:all = off");
// find all long lived particles in pythia
     Int_t n = 1;
     while(n!=0){
      n = fPythia->particleData.nextId(n);
      ParticleDataEntry* p = fPythia->particleData.particleDataEntryPtr(n);
      if (p->tau0()>1){
      string particle = std::to_string(n)+":mayDecay = false";
      fPythia->readString(particle);
      fLogger->Info(MESSAGE_ORIGIN,"Made %s stable for Pythia, should decay in Geant4",p->name().c_str());
      }
     }
  } else {  
   fPythia->setRndmEnginePtr(fRandomEngine);
   fPythia->settings.mode("Beams:idA",  fId);
   fPythia->settings.mode("Beams:idB",  2212);
   fPythia->settings.mode("Beams:frameType",  2);
   fPythia->settings.parm("Beams:eA",fMom);
   fPythia->settings.parm("Beams:eB",0.);
  }
  fPythia->init();
  if (targetName!=""){
   fMaterialInvestigator = new GenieGenerator();
   TGeoVolume* top = gGeoManager->GetTopVolume();
   TGeoNode* target = top->FindNode(targetName);
   if (!target){
       fLogger->Error(MESSAGE_ORIGIN,"target not found, %s, program will crash",targetName.Data());
   }
   Double_t z_middle = target->GetMatrix()->GetTranslation()[2];
   TGeoBBox* sha = (TGeoBBox*)target->GetVolume()->GetShape();
   startZ =  z_middle - sha->GetDZ();
   endZ   =  z_middle + sha->GetDZ();
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
Pythia8Generator::~Pythia8Generator() 
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t Pythia8Generator::ReadEvent(FairPrimaryGenerator* cpg)
{
  Double_t x,y,z,px,py,pz,dl,e,tof;
  Int_t im,id,key;
  fnRetries =0;
// take charm hadrons from external file
// correct eventually for too much primary Ds produced by pythia6
  key=0; 
  bool l = true; 
  while(l){ 
     if (fn==fNevents) {fLogger->Warning(MESSAGE_ORIGIN, "End of input file. Rewind.");}
     fTree->GetEntry((fn+1)%fNevents);
// check that this and next entry is charm, otherwise continue reading
     l = false;
     if (int(mE[0])== 0){ l = true; } 
     bool isDs = false;
     if ( int(fabs(hid[0]) ) == 431){ isDs = true; }   
     fTree->GetEntry(fn%fNevents);
     if (int(mE[0])== 0){ l = true; }   
     fn++;
     if ( int(fabs(hid[0]) ) == 431 || isDs ){
       Double_t rnr = gRandom->Uniform(0,1);
       if( rnr>fFDs ) { 
        l = true;
        fn++;
       }
     }
  }
  Double_t zinter=0;
  if (targetName!=""){
// calculate primary proton interaction point:
// loop over trajectory between start and end to pick an interaction point, copied from GenieGenerator and adapted to hadrons
   Double_t prob2int = -1.;
   Double_t rndm = 0.;
   Double_t sigma;
   Int_t count=0;
   Double_t zinterStart = start[2];
// simulate more downstream interaction points for interactions down in the cascade
   Int_t nInter = ck[0]; if (nInter>16){nInter=16;}
   for( Int_t nI=0; nI<nInter; nI++){
    // if (!subprocCodes[nI]<90){continue;}  //if process is not inelastic, go to next. Changed by taking now collision length
    prob2int = -1.;   
    Int_t intLengthFactor = 1; // for nucleons
    if (TMath::Abs(ancestors[nI]) < 1000){intLengthFactor = 1.16;} // for mesons 
    // Fe: nuclear /\ 16.77 cm pion 20.42 cm  f=1.22
    // W:  nuclear /\ 9.946 cm pion 11.33 cm  f=1.14
    // Mo: nuclear /\ 15.25 cm pion 17.98 cm  f=1.18
    while (prob2int<rndm) {
 //place x,y,z uniform along path
      zinter = gRandom->Uniform(zinterStart,end[2]);
      Double_t point[3]={xOff,yOff,zinter};
      bparam = fMaterialInvestigator->MeanMaterialBudget(start, point, mparam);
      Double_t interLength = mparam[8]  * intLengthFactor * 1.7; // 1.7 = interaction length / collision length from PDG Tables 
      TGeoNode *node = gGeoManager->FindNode(point[0],point[1],point[2]);
      TGeoMaterial *mat = 0;
      if (node && !gGeoManager->IsOutside()) {
         mat = node->GetVolume()->GetMaterial();
         Double_t n = mat->GetDensity()/mat->GetA();
         sigma = 1./(n*mat->GetIntLen())/mbarn;   // no need to multiply with intLengthFactor, will cancel in next equation.
         prob2int = TMath::Exp(-interLength)*sigma/maxCrossSection;
      }else{
         prob2int=0.;
      }
      rndm = gRandom->Uniform(0.,1.); 
      count+=1;
    }
    zinterStart = zinter;
   } 
   zinter = zinter*cm;
  }
  for(Int_t c=0; c<2; c++){
    if(c>0){
      fTree->GetEntry(fn%fNevents);
      fn++;
    }
    fPythia->event.reset();
    id = (Int_t)hid[0];
    fPythia->event.append( id, 1, 0, 0, hpx[0],  hpy[0],  hpz[0],  hE[0],  hM[0], 0., 9. );
//simulate displaced vertex, Pythia8 will not do it
    Double_t tau0 = fPythia->particleData.tau0(id); // ctau in mm
    dl = gRandom->Exp(tau0) / hM[0]; // mm/GeV       
    fPythia->next();
    Int_t addedParticles = 0;
    if(c==0){
// original particle responsible for interaction, "mother of charm" from external file
     px=mpx[0];
     py=mpy[0];
     pz=mpz[0];
     x=0.;
     y=0.;
     z=zinter;
     id=mid[0];
     cpg->AddTrack(id,px,py,pz,x/cm,y/cm,z/cm,-1,false);
     addedParticles +=1;
    }
    for(Int_t ii=1; ii<fPythia->event.size(); ii++){
     id = fPythia->event[ii].id(); 
     Bool_t wanttracking=false;
     if(fPythia->event[ii].isFinal()){ wanttracking=true; }
     if (ii>1){
      z  = fPythia->event[ii].zProd()+dl*fPythia->event[1].pz()+zinter;
      x  = fPythia->event[ii].xProd()+dl*fPythia->event[1].px();
      y  = fPythia->event[ii].yProd()+dl*fPythia->event[1].py();
      tof = fPythia->event[ii].tProd()/ (10*c_light) + dl*fPythia->event[1].e()/cm/c_light;
     }else{
      z  = fPythia->event[ii].zProd()+zinter;
      x  = fPythia->event[ii].xProd();
      y  = fPythia->event[ii].yProd();
      tof = fPythia->event[ii].tProd() / (10*c_light) ; // to go from mm to s
     }
     pz = fPythia->event[ii].pz();
     px = fPythia->event[ii].px();  
     py = fPythia->event[ii].py();  
     e  = fPythia->event[ii].e();
     im = fPythia->event[ii].mother1()+key;

     if (ii==1){im = 0;}
     cpg->AddTrack(id,px,py,pz,x/cm,y/cm,z/cm,im,wanttracking,e,tof,1.);
     addedParticles+=1;
    } 
    key+=addedParticles-1; // pythia counts from 1
  } 
  counter+=1; 
// now the underyling event
  bool lx = true;
  while(lx){      
    fTree->GetEntry(fn%fNevents);
    lx = false;
    if (mE[0] == 0){
     lx = true;
     fn++;
     cpg->AddTrack((Int_t)hid[0],hpx[0],hpy[0],hpz[0],(mpx[0]+fPythia->event[0].xProd())/cm,
                                                      (mpy[0]+fPythia->event[0].yProd())/cm,
                                                      (mpz[0]+fPythia->event[0].zProd())/cm+zinter/cm,-1,true);
     // mpx,mpy,mpz are the vertex coordinates with respect to charm hadron, first particle in Pythia is (system) 
   }
  } 
   
  return kTRUE;
}
// -------------------------------------------------------------------------

ClassImp(Pythia8Generator)
