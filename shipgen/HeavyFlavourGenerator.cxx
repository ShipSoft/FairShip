#include <math.h>
#include <array>
#include "TROOT.h"
#include "Pythia8/Pythia.h"
#include "TMath.h"
#include "TH1F.h"
#include "TH1D.h"
#include "TH2D.h"
#include "HeavyFlavourGenerator.h"
#include "ShipMCTrack.h"
#include "HNLPythia8Generator.h"
#include "TDatabasePDG.h"

// should eventually replace makeCascade.py and makeDecay.py 
// use EvtGen for decay of charm or beauty particles

using namespace Pythia8;

// -----   Default constructor   -------------------------------------------
HeavyFlavourGenerator::HeavyFlavourGenerator() 
{
  fUseRandom1 = kFALSE; 
  fUseRandom3 = kTRUE;
  fSeed = 0;
  fLogger = FairLogger::GetLogger();
  fBoost = 1.;
  withEvtGen = kTRUE;
  fPythia8 =  new Pythia8::Pythia();
  chicc=1.7e-3;     //prob to produce primary ccbar pair/pot
  chibb=1.6e-7;     //prob to produce primary bbbar pair/pot
  setByHand = kFALSE;
}
// -------------------------------------------------------------------------

Bool_t HeavyFlavourGenerator::Init(TString fInName, TString fOutName, Double_t npot) 
{
  nrpotspill = npot;
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();

  std::vector<int> r = { 221, 223,   113, 331, 333};
  std::vector<int> c = { 7, 7, 5, 6, 9}; // decay channel mumu
  fPythia8->setRndmEnginePtr(fRandomEngine);
  fPythia8->settings.mode("Random:seed",fSeed);
  fPythia8->readString("ProcessLevel:all = off");
  fPythia8->readString("Next:numberCount = 10000");
  
// make pions/kaons/lambda stable  
  std::vector<int> s = { 211,321,130,310,3122,3112,3312 };
  for (unsigned int i=0; i<s.size(); ++i) {
    string particle = std::to_string(s[i])+":mayDecay = false";
    fPythia8->readString(particle);
  }
// boost branching fraction of rare di-muon decays
//                       eta  omega rho0  eta' phi   
   if (fBoost > 1.){
    fLogger->Info(MESSAGE_ORIGIN,"Rescale BRs of dimuon decays in Pythia: %f",fBoost);
    for (unsigned int i=0; i<r.size(); ++i) {  
     Pythia8::ParticleDataEntry* V = fPythia8->particleData.particleDataEntryPtr(r[i]);
     Pythia8::DecayChannel ch = V->channel(c[i]);
     if (TMath::Abs(ch.product(0))!=13 || TMath::Abs(ch.product(1))!=13){
      fLogger->Info(MESSAGE_ORIGIN,"this is not the right decay channel: %i %i",r[i],c[i]);
     }else{     
     TString tmp="";
     tmp+=r[i];tmp+=":";tmp+= c[i];
     tmp+=":bRatio =";
     tmp+=fBoost*ch.bRatio();
     fPythia8->readString(tmp.Data());
     }
    }
   }
  fPythia8->init();
  // Initialize EvtGen.
  if (withEvtGen){
   TString DecayFile    = getenv("SIMPATH");DecayFile +="/share/EvtGen/DECAY_2010.DEC";
   TString ParticleFile = getenv("SIMPATH");ParticleFile +="/share/EvtGen/evt.pdl";
   evtgen = new EvtGenDecays(fPythia8, DecayFile.Data(), ParticleFile.Data());
   TString UdecayFile    = getenv("FAIRSHIP");UdecayFile +="/gconfig/USERDECAY.DEC";
   evtgen->readDecayFile(UdecayFile.Data());
  }
  // open output file, make tree with SHiP MCTrack TClonesArray
  fin   = TFile::Open(fInName);
  nTree = (TNtuple*)fin->FindObjectAny("pythia6"); // old format, simple ntuple
  nTree->SetBranchAddress("id",&n_id);
  nTree->SetBranchAddress("px",&n_px);
  nTree->SetBranchAddress("py",&n_py);
  nTree->SetBranchAddress("pz",&n_pz);
  nTree->SetBranchAddress("M",&n_M);
  nTree->SetBranchAddress("E",&n_E);
 
  fout  = TFile::Open(fOutName, "RECREATE");
  nEvents = nTree->GetEntries();
  // Calculate weights, for the whole file.
  // get histogram with number of pot to normalise
  nrcpot=((TH1F*)fin->Get("2"))->GetBinContent(1)/2.;
  // pot are counted double, i.e. for each signal, i.e. pot/2.
  fLogger->Info(MESSAGE_ORIGIN,"Input file: %s   with %i entries, corresponding to nr-pot=%i",fInName.Data(),nEvents,nrcpot);
  fLogger->Info(MESSAGE_ORIGIN,"Output will be written to: %s",fOutName.Data());
  sTree = new TTree("cbmsim","cbmsim");
  MCTracks = new TClonesArray("ShipMCTrack"); 
  Branch_MCTracks = sTree->Branch("MCTrack",MCTracks,32000,-1);
  // book hists for Genie neutrino momentum distrubition, just as check
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
    TString key = TString(idhnu);
    TH1D* Hidhnu = new TH1D(key.Data(),title.Data(),400,0.,400.);
    title = name;title+="  log10-p vs log10-pt";
    key = TString(idhnu+=100);
    TH2D* Hidhnu100 = new TH2D(key.Data(),title.Data(),100,-0.3,1.7,100,-2.,0.5);
    title = name;title+="  log10-p vs log10-pt";
    key = TString(idhnu+200);
    TH2D* Hidhnu200 = new TH2D(key.Data(),title.Data(),25,-0.3,1.7,100,-2.,0.5);
   }
  }
  pot=0.;
  Ecut = 0.;
  //Determine fDs on this file for primaries
  nDsprim=0;
  ntotprim=0;

  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
HeavyFlavourGenerator::~HeavyFlavourGenerator() 
{
}
// -------------------------------------------------------------------------

// -----   Creating the event   ---------------------------------------------
Bool_t HeavyFlavourGenerator::Execute(Int_t N,Int_t nStart)
{
  Double_t wspill;
  Int_t n = nStart,nParts;
  for(Int_t i=0; i<N; i++){
    nTree->GetEvent(n);
    n+=1;
// check if we deal with charm or beauty:
    if (i == 0){ 
     if (!setByHand and n_M>5){ 
      chicc = chibb;
      fLogger->Info(MESSAGE_ORIGIN,"automatic detection of beauty, configured for beauty");
      fLogger->Info(MESSAGE_ORIGIN,"bb cross section / mbias %f",chicc);
     }else{
      fLogger->Info(MESSAGE_ORIGIN,"cc cross section / mbias %f",chicc);
     }
   // convert pot to weight corresponding to one spill of 5e13 pot
     fLogger->Info(MESSAGE_ORIGIN,"weights: %f p.o.t. per spill",nrpotspill);
    }
    wspill = nrpotspill*chicc/nrcpot;
    // sanity check, count number of p.o.t. on input file.
    Double_t pt=TMath::Sqrt( (n_mpx*n_mpx)+(n_mpy*n_mpy));
    // every event appears twice, i.e.
    if (pt<1.e-5 && n_mid==2212){ 
     pot+=+0.5;
     ntotprim+=1;}
    Int_t idabs=int(TMath::Abs(n_id));
    if (idabs==431){ nDsprim+=1;}
    fPythia8->event.reset();
    fPythia8->event.append(int(n_id),1,0,0,n_px,n_py,n_pz,n_E,n_M,0.,9.);
    fPythia8->next();
    if (withEvtGen){evtgen->decay();}
    fPythia8->event.list();
    std::vector<int> p;
    for (Int_t k=0; k<fPythia8->event.size(); k++){
    // ask for stable particles
     if (fPythia8->event[k].isFinal()){
      //select neutrinos and mu
      idabs=int(TMath::Abs(fPythia8->event[k].id()));
      if (idabs>11 && idabs<17 && fPythia8->event[k].e()>Ecut){
        p.push_back(k);
      }
     }
    }
    if (p.size() >0){
     nParts  = MCTracks->GetEntries();
     TClonesArray &ar = *MCTracks;
     new(ar[nParts]) ShipMCTrack(int(n_id),-1,n_px,n_py,n_pz,n_M,0.,0.,0.,0.,0,wspill);   
     for (Int_t l=0; l<p.size(); l++){    
      Int_t k=p[l];
      Pythia8::Particle par = fPythia8->event[k];
      Double_t ptGM = TMath::Sqrt(n_mpx*n_mpx+n_mpy*n_mpy);
      Int_t motherID = 0;
      Double_t time = 0;  
      Int_t procID = 4; // = Decay
      Int_t id = par.id();
      nParts  = MCTracks->GetEntries();
      new(ar[nParts]) ShipMCTrack(id,motherID,par.px(),par.py(),par.pz(),par.m(),0.,0.,0.,time,procID,wspill);
      idabs=int(TMath::Abs(par.id()));
    // count total muons from charm/spill, and within some angluar range..
      if (idabs==16 || idabs==14 || idabs==12){
         Int_t idhnu=idabs+1000;
         if (par.id()<0){ idhnu+=1000;}
         Double_t pt2 = par.px()*par.px()+par.py()*par.py();
         Double_t ptot = TMath::Sqrt(pt2+par.pz()*par.pz());
         Double_t l10ptot = TMath::Min(TMath::Max(TMath::Log10(ptot),-0.3),1.69999);
         Double_t l10pt = TMath::Min(TMath::Max(TMath::Log10(TMath::Sqrt(pt2)),-2.),0.4999);
         ((TH1D*)fout->Get(TString(idhnu)))->Fill(ptot,wspill);                   
         ((TH2D*)fout->Get(TString(idhnu+100)))->Fill(l10ptot,l10pt,wspill);
         ((TH2D*)fout->Get(TString(idhnu+200)))->Fill(l10ptot,l10pt,wspill);
       }
      }
     Branch_MCTracks->Fill();
    }
    if (n==nEvents){
      fLogger->Info(MESSAGE_ORIGIN,"Rewind input file: %i",n);
      n=0;}
    }
  return kTRUE;
}
// -----   finalizing   ---------------------------------------------
Bool_t HeavyFlavourGenerator::Finish()
{
  fout->Write();
  fout->Close();
}

// -------------------------------------------------------------------------
ClassImp(HeavyFlavourGenerator)
