#ifndef PNDGeGENERATOR_H
#define PNDGeGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "TF1.h"                        // for TF1
#include "TVector3.h"                        
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "vector"

class FairPrimaryGenerator;

class GenieGenerator : public FairGenerator
{
 public:
  
  /** default constructor **/
  GenieGenerator();
  
  /** destructor **/
  virtual ~GenieGenerator();
  
  /** public method ReadEvent **/
  Bool_t OldReadEvent(FairPrimaryGenerator*);  
  Bool_t ReadEvent(FairPrimaryGenerator*);  
  virtual Bool_t Init(const char*, int); //!
  virtual Bool_t Init(const char*); //!
  Int_t GetNevents();
  void SetPositions(Double32_t zTa){ ztarget     = zTa;}
  void AddBox(TVector3 dVec, TVector3 box);
 private:
  std::vector<double> Rotate(Double_t x, Double_t y, Double_t z, Double_t px, Double_t py, Double_t pz); 
  Double_t MeanMaterialBudget(const Double_t *start, const Double_t *end, Double_t *mparam);

 private:
  
 protected:
  Double_t Yvessel,Xvessel,Lvessel,ztarget;
  Double_t Ev,pxv,pyv,pzv, El,pxl, pyl, pzl,vtxx,vtxy,vtxz,vtxt;
  Double_t pxf[500], pyf[500], pzf[500];
  Int_t pdgf[500];
  std::vector<TVector3> dVecs;
  std::vector<TVector3> boxs;
  Bool_t cc;
  Int_t nf,neu;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  bool fFirst;
  Double_t fznu0,fznu11,fXnu11,fYnu11;
  Double_t fEntrDz_inner,fEntrDz_outer,fEntrZ_inner,fEntrZ_outer,fEntrA,fEntrB,fL1z,fScintDz;
  ClassDef(GenieGenerator,1);
};

#endif /* !PNDGeGENERATOR_H */
