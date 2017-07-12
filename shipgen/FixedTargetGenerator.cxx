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
#include "Pythia8Plugins/EvtGen.h"
#include "EvtGenBase/EvtSimpleRandomEngine.hh"
#include "EvtGenBase/EvtRandom.hh"
#include "TDatabasePDG.h"
#include "TMCProcess.h"

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
  withEvtGen = kFALSE;
  chicc=1.7e-3;     //prob to produce primary ccbar pair/pot
  chibb=1.6e-7;     //prob to produce primary bbbar pair/pot
  setByHand = kFALSE;
  Debug = kFALSE;
  firstTime = kTRUE;
  Option = "Primary";
}
Bool_t FixedTargetGenerator::InitForCharmOrBeauty(TString fInName, Double_t npot, Int_t nStart)
{
  Option = "charm";
  nrpotspill = npot;
  nEntry = nStart;
  // open input file with charm or beauty
  fin   = TFile::Open(fInName);
  nTree = (TNtuple*)fin->FindObjectAny("pythia6"); // old format, simple ntuple
  nTree->SetBranchAddress("id",&n_id);
  nTree->SetBranchAddress("px",&n_px);
  nTree->SetBranchAddress("py",&n_py);
  nTree->SetBranchAddress("pz",&n_pz);
  nTree->SetBranchAddress("M",&n_M);
  nTree->SetBranchAddress("E",&n_E);
  nTree->SetBranchAddress("mid",&n_mid);
  nTree->SetBranchAddress("mpx",&n_mpx);
  nTree->SetBranchAddress("mpy",&n_mpy);
  nTree->SetBranchAddress("mpz",&n_mpz);
  nTree->SetBranchAddress("mE",&n_mE);
  nEvents = nTree->GetEntries();
  // Calculate weights, for the whole file.
  // get histogram with number of pot to normalise
  nrcpot=((TH1F*)fin->Get("2"))->GetBinContent(1)/2.;
  // pot are counted double, i.e. for each signal, i.e. pot/2.
  fLogger->Info(MESSAGE_ORIGIN,"Input file: %s   with %i entries, corresponding to nr-pot=%i",fInName.Data(),nEvents,nrcpot);
  // book hists for Genie neutrino momentum distribution
  TDatabasePDG* PDG = TDatabasePDG::Instance();
  for(Int_t idnu=12; idnu<18; idnu+=2){
  // nu or anti-nu
   for (Int_t idadd=-1; idadd<3; idadd+=2){
    Int_t idhnu=1000+idnu;
    Int_t idw=idnu;
    if (idadd==-1){
     idhnu+=1000;
     idw=-idnu;
    }
    TString name=PDG->GetParticle(idw)->GetName();
    TString title = name;title+=" momentum (GeV)";
    TString key = "";key+=idhnu;
    TH1D* Hidhnu = new TH1D(key,title,400,0.,400.);
    title = name;title+="  log10-p vs log10-pt";
    key = "";key+=idhnu+100;
    TH2D* Hidhnu100 = new TH2D(key,title,100,-0.3,1.7,100,-2.,0.5);
    title = name;title+="  log10-p vs log10-pt";
    key = "";key+=idhnu+200;
    TH2D* Hidhnu200 = new TH2D(key,title,25,-0.3,1.7,100,-2.,0.5);
   }
  }
  wspill = 1.; // event weight == 1 for primary events
  pot=0.;
  //Determine fDs on this file for primaries
  nDsprim=0;
  ntotprim=0;

  return kTRUE;
}
// -----   Default Init   -------------------------------------------
Bool_t FixedTargetGenerator::Init() 
{
  fPythiaP =  new Pythia8::Pythia();
  if (Option == "Primary"){
   fPythiaN =  new Pythia8::Pythia();
  }else if (Option == "charm" || Option == "beauty") {
   fPythiaP =  new Pythia8::Pythia();
  } else {
   fLogger->Error(MESSAGE_ORIGIN,"Option not known %s, abort",Option);
  }
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();
  std::vector<int> s = { 211,321,130,310,3122,3112,3312 };
  std::vector<int> r = { 221, 223,   113, 331, 333};
  std::vector<int> c = { 7, 7, 5, 6, 9}; // decay channel mumu
  if (Option == "Primary"){
   fPythiaP->settings.mode("Beams:idB",  2212);
   fPythiaN->settings.mode("Beams:idB",  2112);
  }else{
   fPythiaP->readString("ProcessLevel:all = off");
  }
  std::array<Pythia8::Pythia*,2> plist = {fPythiaP,fPythiaN};
  Int_t pcount = 0;
  for(const auto& fPythia : plist) {
   if (pcount == 1 && Option != "Primary"){continue;}
   pcount+=1; 
   fPythia->setRndmEnginePtr(fRandomEngine);
   fPythia->settings.mode("Random:seed",fSeed);
   fPythia->readString("Next:numberCount = 100000");
   if (Option == "Primary"){
    fPythia->settings.mode("Beams:idA",  2212);
    fPythia->settings.mode("Beams:frameType",  2);
    fPythia->settings.parm("Beams:eA",fMom);
    fPythia->settings.parm("Beams:eB",0.);
    fPythia->readString("SoftQCD:inelastic = on");
    fPythia->readString("PhotonCollision:gmgm2mumu = on");
    fPythia->readString("PromptPhoton:all = on");
    fPythia->readString("WeakBosonExchange:all = on");
   }
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
     TString tmp="";
     tmp+=r[i];tmp+=":";tmp+= c[i];
     tmp+=":bRatio =";
     tmp+=fBoost*ch.bRatio();
     fPythia->readString(tmp.Data());
     }
    }
   }
   fPythia->init();
  }
  // Initialize EvtGen.
  if (withEvtGen){
   TString DecayFile    = getenv("SIMPATH");DecayFile +="/share/EvtGen/DECAY.DEC";
   TString ParticleFile = getenv("SIMPATH");ParticleFile +="/share/EvtGen/evt.pdl";
   EvtAbsRadCorr *fsrPtrIn = 0;
   EvtExternalGenList *extPtr = new EvtExternalGenList();
   std::list<EvtDecayBase*> models = extPtr->getListOfModels();
 // Define the random number generator
   EvtRandomEngine* eng = new EvtSimpleRandomEngine();
   EvtRandom::setRandomEngine(eng);
   EvtGen *myEvtGenPtr = new EvtGen(DecayFile.Data(), ParticleFile.Data(),eng, fsrPtrIn, &models, 1, false);
   TString UdecayFile    = getenv("FAIRSHIP");UdecayFile +="/gconfig/USERDECAY.DEC";
   evtgenP = new EvtGenDecays(fPythiaP, DecayFile.Data(), ParticleFile.Data(),myEvtGenPtr);
   evtgenP->readDecayFile(UdecayFile.Data()); // will make update of EvtGen with user decay file
   // use one instance of EvtGen, requires patch to Pythia8Plugins/EvtGen.h
   if (Option == "Primary"){
    evtgenN = new EvtGenDecays(fPythiaN, DecayFile.Data(), ParticleFile.Data(),myEvtGenPtr);
   }
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
  Pythia8::Pythia* fPythia;
  if (G4only){
   cpg->AddTrack(2212,0.,0.,fMom,xOff/cm,yOff/cm,zinter/cm,-1,kTRUE,-1.,0.,1.);  
  }else if (Option == "Primary"){
   if (gRandom->Uniform(0.,1.) < ZoverA ){
    fPythiaP->next();
    if (withEvtGen){evtgenP->decay();}
    fPythia = fPythiaP;
   }else{
    fPythiaN->next();
    if (withEvtGen){evtgenN->decay();}
    fPythia = fPythiaN;
   }
  }else{
    if (nEntry==nEvents){
      fLogger->Info(MESSAGE_ORIGIN,"Rewind input file: %i",nEntry);
      nEntry=0;}
    nTree->GetEvent(nEntry);
    nEntry+=1;
// check if we deal with charm or beauty:
    if (firstTime){ 
     if (!setByHand and n_M>5){ 
      chicc = chibb;
      fLogger->Info(MESSAGE_ORIGIN,"automatic detection of beauty, configured for beauty");
      fLogger->Info(MESSAGE_ORIGIN,"bb cross section / mbias %f",chicc);
     }else{
      fLogger->Info(MESSAGE_ORIGIN,"cc cross section / mbias %f",chicc);
     }
   // convert pot to weight corresponding to one spill of 5e13 pot
     fLogger->Info(MESSAGE_ORIGIN,"weights: %f p.o.t. per spill",nrpotspill);
     wspill = nrpotspill*chicc/nrcpot;
     firstTime = kFALSE;
    }
    // sanity check, count number of p.o.t. on input file.
    Double_t pt=TMath::Sqrt( (n_mpx*n_mpx)+(n_mpy*n_mpy));
    // every event appears twice, i.e.
    if (pt<1.e-5 && n_mid==2212){ 
     pot+=+0.5;
     ntotprim+=1;}
    Int_t idabs=int(TMath::Abs(n_id));
    if (idabs==431){ nDsprim+=1;}
    fPythiaP->event.reset();
    fPythiaP->event.append(int(n_id),1,0,0,n_px,n_py,n_pz,n_E,n_M,0.,9.);
    TMCProcess procID  = kPTransportation;
    if (n_mid==2212 && (n_mpx*n_mpx+n_mpy*n_mpy)<1E-5) {procID = kPPrimary;} // probably primary and not from cascade
    cpg->AddTrack(int(n_mid),n_mpx,n_mpy,n_mpz, xOff/cm,yOff/cm,zinter/cm,-1,kFALSE,n_mE,0.,wspill,procID);
    fPythiaP->next();
    fPythia = fPythiaP;
  }
  if (withEvtGen){fPythiaP->moreDecays();} // let the very short lived resonances decay via Pythia8
  if(Debug){fPythia->event.list();}
  TMCProcess procID;
  for(Int_t ii=1; ii<fPythia->event.size(); ii++){
     Double_t  e = fPythia->event[ii].e();
     Double_t  m = fPythia->event[ii].m();
     Double_t pz = fPythia->event[ii].pz();
     Int_t id = fPythia->event[ii].id(); 
     Bool_t wanttracking=kTRUE;
     if (e-m<EMax || !fPythia->event[ii].isFinal() || pz<0) {wanttracking=kFALSE;}
     Double_t z  = fPythia->event[ii].zProd()+zinter;
     Double_t x  = fPythia->event[ii].xProd()+xOff;
     Double_t y  = fPythia->event[ii].yProd()+yOff;
     Double_t tof = fPythia->event[ii].tProd();
     Double_t px = fPythia->event[ii].px();  
     Double_t py = fPythia->event[ii].py();  
     Int_t im = fPythia->event[ii].mother1()-1+1;
     procID = kPPrimary;
     if (Option != "Primary"){
        procID = kPDecay;
        if (ii==1) {procID  = kPHadronic;}
     }
     cpg->AddTrack(id,px,py,pz,x/cm,y/cm,z/cm,im,wanttracking,e,tof,wspill,procID);
    }    
  return kTRUE;
}
// -------------------------------------------------------------------------

ClassImp(FixedTargetGenerator)
