#ifndef PNDH8GENERATOR_H
#define PNDH8GENERATOR_H 1

#include "TROOT.h"
#include "TString.h"
#include "TFile.h"
#include "TTree.h"
#include "FairGenerator.h"
#include "Pythia8/Pythia.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;
//using namespace Pythia8;

class PyTr1Rng : public Pythia8::RndmEngine
{
 public:
  PyTr1Rng() {  rng = new TRandom1(gRandom->GetSeed()); };
  virtual ~PyTr1Rng() {};
  
  Double_t flat() { return rng->Rndm(); };
  
 private:
  TRandom1 *rng; //!
};

class PyTr3Rng : public Pythia8::RndmEngine
{
 public:
  PyTr3Rng() {  rng = new TRandom3(gRandom->GetSeed()); };
  virtual ~PyTr3Rng() {};
  
  Double_t flat() { return rng->Rndm(); };
  
 private:
  TRandom3 *rng; //!
};



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
  void Print(){fPythia->settings.listAll(); };  //!
  void List(int id){fPythia->particleData.list(id);}; //!
  
  virtual Bool_t Init(); //!
  
  void SetMom(Double_t mom) { fMom = mom; };
  void SetId(Double_t id) { fId  = id; };
  void SetHNLId(Int_t id) { fHNL = id; };
  void SetLmin(Double_t z) { fLmin = z*10; };
  void SetLmax(Double_t z) { fLmax = z*10; };
  void SetSmearBeam(Double_t sb) { fsmearBeam = sb; };
  void SetfFDs(Double_t z) { fFDs = z; };
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void UseExternalFile(const char* x, Int_t i){ fextFile   = x; firstEvent=i; };
  void UseDeepCopy(){ fDeepCopy   = kTRUE; };
  Int_t nrOfRetries(){ return fnRetries; };
  Pythia8::Pythia* getPythiaInstance(){return fPythia;};
  Pythia8::Pythia* fPythia;             //!
 private:
  
  Pythia8::RndmEngine* fRandomEngine;  //!
  
 protected:

  Double_t fMom;       // proton momentum
  Int_t    fHNL;       // HNL ID
  Int_t    fId;        // target type
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Double_t fLmin;      // m minimum  decay position z
  Double_t fLmax;      // m maximum decay position z
  Int_t fnRetries;     // number of events without any HNL 
  Double_t fctau;      // hnl lifetime 
  Double_t fFDs;       // correction for Pythia6 to match measured Ds production
  Double_t fsmearBeam; // finite beam size
  const char* fextFile; // read charm and beauty hadrons from external file, decay with Pythia
  TFile* fInputFile;   //! pointer to a file
  TTree* fTree;        //! 
  Int_t  fNevents,fn,firstEvent,fShipEventNr;
  Float_t hpx[1], hpy[1], hpz[1], hE[1],hM[1],mpx[1], mpy[1], mpz[1], mE[1],hid[1], mid[1];
  Bool_t fDeepCopy;    // not used
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command

  ClassDef(HNLPythia8Generator,6);
};

#endif /* !PNDH8GENERATOR_H */
