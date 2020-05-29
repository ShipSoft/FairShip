#ifndef FIXEDTARGETGENERATOR_H
#define FIXEDTARGETGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "Pythia8/Pythia.h"
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "TTree.h"
#include "TNtuple.h"
#include "GenieGenerator.h"

class FairPrimaryGenerator;
class EvtGenDecays;

class FixedTargetGenerator : public FairGenerator
{
 public:
  
  /** default constructor **/
  FixedTargetGenerator();
  
  /** destructor **/
  virtual ~FixedTargetGenerator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  void SetParameters(char*);
  void Print(); //!
  
  virtual Bool_t Init(); //!
  Bool_t InitForCharmOrBeauty(TString fInName, Int_t nev, Double_t npots=5E13, Int_t nStart=0); //!
  
  void SetMom(Double_t mom) { fMom = mom; };
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void SetCharmTarget(Bool_t charmtarget = true) {fcharmtarget = charmtarget;}; //charm geometry uses a different target, default one is usual
  void SetTarget(TString s, Double_t x,Double_t y ) { targetName = s; xOff=x; yOff=y; };
  void SetBoost(Double_t f) { fBoost  = f; }  // boost factor for rare di-muon decays
  void SetG4only() { G4only  = true; }  // only run Geant4, no pythia primary interaction
  void SetTauOnly() { tauOnly  = true; }  // only have Ds decay to tau 
  void SetJpsiMainly() { JpsiMainly  = true; }  // let all Jpsi decay to mumu
  void WithEvtGen() { withEvtGen = true;} // use EvtGen as external decayer to Pythia, experimental phase, only works for one Pythia instance
  void SetChibb(Double_t x) { chibb = x; }  // chibb = bbbar over mbias cross section   
  void SetChicc(Double_t x) { chicc = x; }  // chicc = ccbar over mbias cross section   
  inline void SetSeed(Double_t seed){fSeed=seed;}
  inline void SetHeartBeat(Int_t x){heartbeat=x;}
  inline void SetEnergyCut(Float_t emax) {EMax=emax;}// min energy to be copied to Geant4
  inline void SetDebug(Bool_t x){Debug=x;}
  Double_t GetPotForCharm(){return nrpotspill/wspill;}
  Pythia8::Pythia* GetPythia() {return fPythiaP;}
 private:
  
 Pythia8::RndmEngine* fRandomEngine;  //!
   
 protected:

  Double_t fMom;       // proton momentum
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Double_t fSeed,EMax,fBoost,chicc,chibb,wspill,nrpotspill;
  Int_t nEvents,nEntry,pot,nDsprim,ntotprim;      
  Bool_t tauOnly,JpsiMainly,G4only,setByHand,Debug,withEvtGen;
  Bool_t fcharmtarget;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  Pythia8::Pythia* fPythiaN;            //!
  Pythia8::Pythia* fPythiaP;            //!
  EvtGenDecays* evtgenN;            //!
  EvtGenDecays* evtgenP;            //!
  GenieGenerator* fMaterialInvestigator;  //!
  TString targetName,Option;
  Double_t xOff;
  Double_t yOff;
  Double_t start[3];
  Double_t end[3];
  Double_t bparam;
  Double_t mparam[10];
  Double_t startZ;
  Double_t endZ;
  Double_t maxCrossSection;
  TFile* fin;//!
  TNtuple* nTree;//!
  Float_t  n_id,n_px,n_py,n_pz,n_M,n_E,n_mpx,n_mpy,n_mpz,n_mE,n_mid,ck;
  Int_t heartbeat;

  ClassDef(FixedTargetGenerator,2);
};
#endif /* !FIXEDTARGETGENERATOR_H */
