#ifndef PNDH8GENERATOR_H
#define PNDH8GENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "Pythia.h"
#include "TRandom1.h"
#include "TRandom3.h"

class FairPrimaryGenerator;
using namespace Pythia8;


class HNLPythia8Generator : public FairGenerator
{
 public:
  
  /** default constructor **/
  HNLPythia8Generator();
  
  /** destructor **/
  virtual ~HNLPythia8Generator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  void SetParameters(char*);
  void Print(){fPythia.settings.listAll(); };  //!
  void List(int id){fPythia.particleData.list(id);}; //!
  
  virtual Bool_t Init(); //!
  
  void SetMom(Double_t mom) { fMom = mom; };
  void SetId(Double_t id) { fId  = id; };
  void SetHNLId(Int_t id) { fHNL = id; };
  void SetLmin(Int_t z) { fLmin = z; };
  void SetLmax(Int_t z) { fLmax = z; };
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void UseDeepCopy(){ fDeepCopy   = kTRUE; };
  void getPythiaInstance(){cout<<"fPythia"<<&fPythia<<endl;};
 private:
  
  Pythia fPythia;             //!
  RndmEngine* fRandomEngine;  //!
  // doesnot work Pythia8::Pythia getPythiaInstance(){return fPythia;}  //!
  
 protected:

  Double_t fMom;       // proton momentum
  Int_t    fHNL;       // HNL ID
  Int_t    fId;        // target type
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Double_t fLmin;      // m minimum  decay position z
  Double_t fLmax;      // m maximum decay position z
  Double_t fctau ;     // hnl lifetime 
  Bool_t fDeepCopy;    // not used

  ClassDef(HNLPythia8Generator,1);
};

#endif /* !PNDH8GENERATOR_H */
