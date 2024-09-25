#ifndef EVTCALCGENERATOR_H
#define EVTCALCGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;

class EvtCalcGenerator : public FairGenerator
{
 public:

  /** default constructor **/
  EvtCalcGenerator();

  /** destructor **/
  virtual ~EvtCalcGenerator();

  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  virtual Bool_t Init(const char*, int); //!
  virtual Bool_t Init(const char*); //!

  Int_t GetNevents()
  {
    return fNevents;
  }

  void SetPositions(Double_t zTa=-5814.25, Double_t zDV=0.){
    ztarget      = zTa; // units cm (midpoint)
    zDecayVolume = zDV; // units cm (midpoint)
  }

 private:

 protected:
  Int_t pdg_lpp, pdg_prod1, pdg_prod2, pdg_prod3;
  Double_t px_llp, py_llp, pz_llp, e_llp;
  Double_t vx, vy, vz, decay_prob;
  Double_t px_prod1, py_prod1, pz_prod1, e_prod1;
  Double_t px_prod2, py_prod2, pz_prod2, e_prod2;
  Double_t px_prod3, py_prod3, pz_prod3, e_prod3;
  Double_t ztarget, zDecayVolume = zDV;
  TFile* fInputFile;
  TTree* fTree;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  int fNevents;
  int fn;
  ClassDef(EvtCalcGenerator,1);
};

#endif /* !EVTCALCGENERATOR_H */
