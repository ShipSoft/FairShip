#ifndef PNDMuGENERATOR_H
#define PNDMuGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "TF1.h"                        // for TF1
#include "TClonesArray.h"         
#include "TVector3.h"                        
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "vector"

class FairPrimaryGenerator;

class MuDISGenerator : public FairGenerator
{
 public:
  
  /** default constructor **/
  MuDISGenerator();
  
  /** destructor **/
  virtual ~MuDISGenerator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);  
  virtual Bool_t Init(const char*, int); //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();
 private:
  
 protected:
  TClonesArray* iMuon ;
  TClonesArray* dPart ; 
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  bool fFirst;
  ClassDef(MuDISGenerator,1);
};
#endif /* !PNDMuGENERATOR_H */
