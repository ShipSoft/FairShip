#ifndef PNDP8GENERATOR_H
#define PNDP8GENERATOR_H 1
// Avoid the inclusion of dlfcn.h by Pyhtia.h that CINT is not able to process
#ifdef __CINT__
#define _DLFCN_H_
#define _DLFCN_H
#endif

#include "TROOT.h"
#include "FairGenerator.h"
#include "Pythia.h"
#include "TRandom1.h"
#include "TRandom3.h"

class FairPrimaryGenerator;
using namespace Pythia8;

class PyTr1Rng : public RndmEngine
{
 public:
  PyTr1Rng() {  rng = new TRandom1(gRandom->GetSeed()); };
  virtual ~PyTr1Rng() {};
  
  Double_t flat() { return rng->Rndm(); };
  
 private:
  TRandom1 *rng; //!
};

class PyTr3Rng : public RndmEngine
{
 public:
  PyTr3Rng() {  rng = new TRandom3(gRandom->GetSeed()); };
  virtual ~PyTr3Rng() {};
  
  Double_t flat() { return rng->Rndm(); };
  
 private:
  TRandom3 *rng; //!
};




class Pythia8Generator : public FairGenerator
{
 public:
  
  /** default constructor **/
  Pythia8Generator();
  
  /** destructor **/
  virtual ~Pythia8Generator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  void SetParameters(char*);
  void Print(); //!
  
  virtual Bool_t Init(); //!
  
  void SetMom(Double_t mom) { fMom = mom; };
  void SetId(Double_t id) { fId  = id; };
  void SetHNLId(Int_t id) { fHNL = id; };
  void UseDeepCopy(){ fDeepCopy   = kTRUE; };
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void GetPythiaInstance(int);

 private:
  
  Pythia fPythia;             //!
  RndmEngine* fRandomEngine;  //!
  
 protected:

  Double_t fMom;       // proton momentum
  Int_t    fHNL;       // HNL ID
  Int_t    fId;       // target type
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Bool_t fDeepCopy;    // copy complete pythia event 

  ClassDef(Pythia8Generator,1);
};

#endif /* !PNDP8GENERATOR_H */
