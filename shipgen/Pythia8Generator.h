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
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "TTree.h"

class FairPrimaryGenerator;
using namespace Pythia8;

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
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void UseExternalFile(const char* x, Int_t i){ fextFile   = x; firstEvent=i; };
  void SetfFDs(Double_t z) { fFDs = z; };
  Int_t nrOfRetries(){ return fnRetries; };

 private:
  
  RndmEngine* fRandomEngine;  //!
  
 protected:

  Double_t fMom;       // proton momentum
  Int_t    fId;       // target type
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  const char* fextFile; // read charm and beauty hadrons from external file, decay with Pythia
  Float_t hpx[1], hpy[1], hpz[1], hE[1],hM[1],mpx[1], mpy[1], mpz[1], mE[1],hid[1], mid[1];
  Int_t  fNevents,fn,firstEvent,fShipEventNr;
  TFile* fInputFile;   //! pointer to a file
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TTree* fTree;        //! 
  Pythia* fPythia;             //!
  Double_t fFDs;       // correction for Pythia6 to match measured Ds production
  Int_t fnRetries;     // 
  ClassDef(Pythia8Generator,1);
};

#endif /* !PNDP8GENERATOR_H */
