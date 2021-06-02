#ifndef FLUKAntGENERATOR_H
#define FLUKAntGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree

class FairPrimaryGenerator;

class NtupleGenerator_FLUKA : public FairGenerator
{
 public:
  
  /** default constructor **/
  NtupleGenerator_FLUKA();
  
  /** destructor **/
  virtual ~NtupleGenerator_FLUKA();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);  
  virtual Bool_t Init(const char*, int); //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();
  void SetZ(Double_t X) {  SND_Z = X; };
 private:
  
 protected:
  Double_t id[1],generation[1],E[1],t[1],px[1],py[1],pz[1],x[1],y[1],z[1],w[1],SND_Z;
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  ClassDef(NtupleGenerator_FLUKA,2);
};

#endif /* !FLUKAntGENERATOR_H */
