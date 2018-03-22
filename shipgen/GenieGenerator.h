#ifndef PNDGeGENERATOR_H
#define PNDGeGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "TF1.h"                        // for TF1
#include "TH1.h"                        // for TH1
#include "TH2.h"                        // for TH2
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
  void NuOnly(){fNuOnly = true;}
  void SetPositions(Double_t zTa, Double_t zS=-3400., Double_t zE=2650.){ 
    ztarget     = zTa;
    startZ      = zS;
    endZ        = zE; 
  }
  void AddBox(TVector3 dVec, TVector3 box);
  Double_t MeanMaterialBudget(const Double_t *start, const Double_t *end, Double_t *mparam);
 private:
  std::vector<double> Rotate(Double_t x, Double_t y, Double_t z, Double_t px, Double_t py, Double_t pz); 

 private:
  
 protected:
  Double_t Yvessel,Xvessel,Lvessel,ztarget,startZ,endZ;
  Double_t Ev,pxv,pyv,pzv, El,pxl, pyl, pzl,vtxx,vtxy,vtxz,vtxt;
  Double_t Ef[500], pxf[500], pyf[500], pzf[500];
  Int_t pdgf[500];
  std::vector<TVector3> dVecs;
  std::vector<TVector3> boxs;
  Bool_t cc, nuel;
  Int_t nf,neu;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  bool fFirst,fNuOnly;
  Double_t fznu0,fznu11,fXnu11,fYnu11;
  Double_t fEntrDz_inner,fEntrDz_outer,fEntrZ_inner,fEntrZ_outer,fEntrA,fEntrB,fL1z,fScintDz;
  TH1D* pxhist[3000];//!
  TH1D* pyslice[3000][100];//!

  ClassDef(GenieGenerator,1);
};

#endif /* !PNDGeGENERATOR_H */
