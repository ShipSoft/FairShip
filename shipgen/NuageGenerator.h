#ifndef NUAGEGENERATOR_H
#define NUAGEGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TTree.h"                      // for TTree
#include "TF1.h"                        // for TF1
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "vector"
#include "TVector3.h"

class FairPrimaryGenerator;

class NuageGenerator : public FairGenerator
{
public:
    
    /** default constructor **/
    NuageGenerator();
    
    /** destructor **/
    virtual ~NuageGenerator();
    
    /** public method ReadEvent **/
    Bool_t ReadEvent(FairPrimaryGenerator*);
    virtual Bool_t Init(const char*, int); //!
    virtual Bool_t Init(const char*); //!
    Int_t GetNevents();
    void NuOnly(){fNuOnly = true;}
    void SetPositions(Double_t zTa, Double_t zS=-3400., Double_t zE=2650., Double_t xS = 0, Double_t xE = 0, Double_t yS = 0, Double_t yE=0 ){
        ztarget     = zTa;
        startZ      = zS;
        endZ        = zE;
	startX      = xS;
        endX        = xE;
	startY      = yS;
        endY        = yE;
    }
    void AddBox(TVector3 dVec, TVector3 box);
    
    
private:
    std::vector<double> Rotate(Double_t x, Double_t y, Double_t z, Double_t px, Double_t py, Double_t pz);
    Double_t MeanMaterialBudget(const Double_t *start, const Double_t *end, Double_t *mparam);
    
protected:
    Double_t Yvessel,Xvessel,Lvessel,ztarget,startZ,endZ, startX,endX, startY,endY;
    Float_t Ev,pxv,pyv,pzv, El,pxl, pyl, pzl,vtxx,vtxy,vtxz,vtxt;
//Float_t vtxx1, vtxy1,vtxz1,vtxt1; // position of secondary vtx
    Float_t pxf[500], pyf[500], pzf[500];
    Float_t pdgf[500];
    std::vector<TVector3> dVecs;
    std::vector<TVector3> boxs;
    Int_t cc;
    Int_t nf,neu;
//	Int_t nvtx;
    FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
    TFile* fInputFile;
    TTree* fTree;
    int fNevents;
    int fn;
    bool fFirst, fNuOnly;
    //  Double_t fznu0,fznu11,fXnu11,fYnu11;
    Double_t fznu,fXnu,fYnu;
    Double_t fEntrDz_inner,fEntrDz_outer,fEntrZ_inner,fEntrZ_outer,fEntrA,fEntrB,fL1z,fScintDz;
    ClassDef(NuageGenerator,1);
};

#endif /* !PNDGeGENERATOR_H */
