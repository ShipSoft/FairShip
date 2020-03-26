#ifndef ALPACAGENERATOR_H
#define ALPACAGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;

class ALPACAGenerator : public FairGenerator
{
 public:
  
  /** default constructor **/
  ALPACAGenerator();
  
  /** destructor **/
  virtual ~ALPACAGenerator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);  
  virtual Bool_t Init(const char*, int); //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();
 private:
  
 protected:
  Float_t pdg,parent,event,track;
  Float_t e,tof,x,y,z,px,py,pz;
  Float_t w;
  TFile* fInputFile;
  TTree* fTree;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  int fNevents;
  int fn;
  ClassDef(ALPACAGenerator,1);
};

#endif /* !ALPACAGENERATOR_H */
