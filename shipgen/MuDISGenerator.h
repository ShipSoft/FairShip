#ifndef SHIPGEN_MUDISGENERATOR_H_
#define SHIPGEN_MUDISGENERATOR_H_ 1

#include "FairGenerator.h"
#include "FairLogger.h"   // for FairLogger, MESSAGE_ORIGIN
#include "TClonesArray.h"
#include "TF1.h"   // for TF1
#include "TROOT.h"
#include "TTree.h"   // for TTree
#include "TVector3.h"
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
    virtual Bool_t Init(const char*, int);   //!
    virtual Bool_t Init(const char*);        //!
    Int_t GetNevents();

    void SetPositions(Double_t z_start, Double_t z_end, Double_t x_start, Double_t x_end, Double_t y_start, Double_t y_end)
    {
      startZ = z_start;
      endZ = z_end;
      startX = x_start;
      endX = x_end;
      startY = y_start;
      endY = y_end;
    }

    Double_t MeanMaterialBudget(const Double_t* start, const Double_t* end, Double_t* mparam);

 protected:
  Double_t startZ, endZ, startX, endX, startY, endY;
  TClonesArray* iMuon ;
  TClonesArray* dPart ;
  TClonesArray* dPartSoft ;
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  bool fFirst;
  const Double_t c_light = 29.9792458;//speed of light in cm/ns
  const Double_t muon_mass = 0.10565999895334244;  //muon mass in GeV
  ClassDef(MuDISGenerator, 2);
};
#endif   // SHIPGEN_MUDISGENERATOR_H_
