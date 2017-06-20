#ifndef FIXEDTARGETGENERATOR_H
#define FIXEDTARGETGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "Pythia.h"
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "TTree.h"
#include "GenieGenerator.h"

class FairPrimaryGenerator;
using namespace Pythia8;

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
  
  void SetMom(Double_t mom) { fMom = mom; };
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void SetTarget(TString s, Double_t x,Double_t y ) { targetName = s; xOff=x; yOff=y; };
  void SetBoost(Double_t f) { fBoost  = f; }  // boost factor for rare di-muon decays
  inline void SetSeed(Double_t seed){fSeed=seed;}
  inline void SetEnergyCut(Float_t emax) {EMax=emax;}// min energy to be copied to Geant4

 private:
  
  RndmEngine* fRandomEngine;  //!
  
 protected:

  Double_t fMom;       // proton momentum
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Double_t fSeed,EMax,fBoost;
  Bool_t tauOnly,JpsiMainly;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  Pythia* fPythiaN;            //!
  Pythia* fPythiaP;            //!
  GenieGenerator* fMaterialInvestigator;  //!
  TString targetName;
  Double_t xOff;
  Double_t yOff;
  Double_t start[3];
  Double_t end[3];
  Double_t bparam;
  Double_t mparam[10];
  Double_t startZ;
  Double_t endZ;
  Double_t maxCrossSection;

  ClassDef(FixedTargetGenerator,0);
};

#endif /* !FIXEDTARGETGENERATOR_H */
