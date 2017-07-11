#ifndef HEAVYFLAVOURGENERATOR_H
#define HEAVYFLAVOURGENERATOR_H 1

#ifndef Pythia8_EvtGen_H
#define Pythia8_EvtGen_H 1
#endif

#include "TROOT.h"
#include "Pythia.h"
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "TTree.h"
#include "TNtuple.h"
#include "TFile.h"
#include "TClonesArray.h"

#include "Pythia8Plugins/EvtGen.h"

using namespace Pythia8;

class HeavyFlavourGenerator 
{
 public:
  
  /** default constructor **/
  HeavyFlavourGenerator();
  
  /** destructor **/
  virtual ~HeavyFlavourGenerator();
  
  /** public method ReadEvent **/
  Bool_t Init(TString fInName, TString fOutName, Double_t npots=5E13);
  Bool_t Finish();
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void WithEvtGen() { withEvtGen = true;} // use EvtGen as external decayer to Pythia
  inline void SetSeed(Double_t seed){fSeed=seed;}
  Bool_t Execute(Int_t nEvents,Int_t nStart=0);
  void SetChicc(Double_t x) { chicc = x;}
  void SetChibb(Double_t x) { chibb = x;}
 private:
  
  RndmEngine* fRandomEngine;  //!
  
 protected:

  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Double_t fSeed,fBoost,chicc,chibb,Ecut;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  Pythia* fPythia8;            //!
  Bool_t withEvtGen, setByHand;
  EvtGenDecays* evtgen;        //!
  Int_t nEvents,pot,nDsprim,ntotprim,nrpotspill,nrcpot;      //!
  TClonesArray* MCTracks; //!
  TBranch* Branch_MCTracks; //!
  TFile* fin;
  TFile* fout;
  TNtuple* nTree;
  Float_t   n_id,n_px,n_py,n_pz,n_M,n_E,n_mpx,n_mpy,n_mpz,n_mid;
  TTree* sTree;
  ClassDef(HeavyFlavourGenerator,0);
};
#endif /* !HEAVYFLAVOURGENERATOR_H */
