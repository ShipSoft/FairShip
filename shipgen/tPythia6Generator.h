#ifndef PNDP6GENERATOR_H
#define PNDP6GENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TPythia6.h"
#include "TString.h"

class FairPrimaryGenerator;

class tPythia6Generator : public FairGenerator
{
 public:
  
  /** default constructor **/
  tPythia6Generator();
  
  /** destructor **/
  virtual ~tPythia6Generator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  
  virtual Bool_t Init(); //!
  
  void SetMom(Double_t mom) { fMom = mom; };
  void SetTarget(TString Type, TString Target) { fType = Type; fTarget=Target;};
  void UseDeepCopy(){ fDeepCopy   = kTRUE; };
 private:
  
  TPythia6* fPythia;           //
  
 protected:
  
  Double_t fMom;       // proton momentum
  Bool_t fDeepCopy;    // copy complete pythia event 
  Bool_t fPionKaonDecay;
  TString fType;   // muon proton scattering 
  TString fTarget;
  ClassDef(tPythia6Generator,1);
};

#endif /* !PNDP6GENERATOR_H */
