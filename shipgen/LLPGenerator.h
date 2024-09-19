#ifndef LLPGENERATOR_H
#define LLPGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;

class LLPGenerator : public FairGenerator
{
 public:

  /** default constructor **/
  LLPGenerator();

  /** destructor **/
  virtual ~LLPGenerator();

  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  virtual Bool_t Init(const char*, int); //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();

  void SetPositions(Double_t zTa=-5814.25, Double_t zDV=0.){
    ztarget      = zTa; // units cm (midpoint)
    zDecayVolume = zDV; // units cm (midpoint)
  }

 private:

 protected:
  Int_t id, Nmeas, volid[500], procid[500], parentid;
  Float_t Ezero,tof;
  Double_t w;
  Float_t px[500], py[500], pz[500], vx[500], vy[500], vz[500];
  TFile* fInputFile;
  TTree* fTree;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  int fNevents;
  int fn;
  ClassDef(LLPGenerator,1);
};

#endif /* !LLPGENERATOR_H */
