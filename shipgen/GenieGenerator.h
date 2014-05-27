#ifndef PNDGeGENERATOR_H
#define PNDGeGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "TF1.h"                        // for TF1
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;

class GenieGenerator : public FairGenerator
{
 public:
  
  /** default constructor **/
  GenieGenerator();
  
  /** destructor **/
  virtual ~GenieGenerator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);  
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();
 private:
  
 protected:
  Double_t Ev,pxv,pyv,pzv, El,pxl, pyl, pzl,vtxx,vtxy,vtxz,vtxt;
  Double_t pxf[500], pyf[500], pzf[500];
  Int_t pdgf[500];
  Int_t nf,neu;
  FairLogger*  fLogger;
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  ClassDef(GenieGenerator,1);
};

#endif /* !PNDGeGENERATOR_H */
