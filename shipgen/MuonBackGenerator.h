#ifndef PNDmuGENERATOR_H
#define PNDmuGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN

class FairPrimaryGenerator;

class MuonBackGenerator : public FairGenerator
{
 public:
  
  /** default constructor **/
  MuonBackGenerator();
  
  /** destructor **/
  virtual ~MuonBackGenerator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);  
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();
  void CloseFile();
 private:
  
 protected:
  Float_t id,parentid,pythiaid,w,px,py,pz,vx,vy,vz;
  TFile* fInputFile;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TTree* fTree;
  int fNevents;
  int fn;
  ClassDef(MuonBackGenerator,1);
};

#endif /* !PNDmuGENERATOR_H */
