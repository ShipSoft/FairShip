#ifndef MYGENERATOR_H
#define MYGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;

class MyGenerator : public FairGenerator
{
 public:

  /** default constructor **/
  MyGenerator();

  /** destructor **/
  virtual ~MyGenerator();

  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  virtual Bool_t Init(const char*, int); //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();
 private:

 protected:

  Double_t px, py, pz, vx, vy, vz;
  TFile* fInputFile;
  TTree* fTree;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  int fNevents;
  int fn;
  Int_t id;
  ClassDef(MyGenerator,1);
};

#endif /* !MYGENERATOR_H */
