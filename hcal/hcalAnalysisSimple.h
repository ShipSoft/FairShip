#ifndef HCALANALYSISCALIB_H
#define HCALANALYSISCALIB_H

#include "FairTask.h"

#include "TString.h"

#include <list>

class TTree;
class hcalStructure;
class TClonesArray;

class hcalAnalysisSimple : public FairTask
{
public:
  hcalAnalysisSimple(const char* name, const Int_t iVerbose);

  /** Default constructor **/
  hcalAnalysisSimple();

  /** Initing routine **/
  virtual InitStatus Init();

  /** Loop procedure **/
  virtual void Exec(Option_t* option);

  /** Finishing routine **/
  virtual void Finish();

  /** Destructor **/
  virtual ~hcalAnalysisSimple() {};

private:
  TTree* fTree;
  Double_t fX;
  Double_t fY;
  Double_t fCX;
  Double_t fCY;
  Double_t fP;
  Double_t fCE;
  Double_t fCE2;
  Double_t fOE;
  Double_t fPX;
  Double_t fPY;
  Double_t fPZ;
  Int_t fEv;
  Int_t fModuleNum;
  Int_t fADC;
  void InitTree();
  hcalStructure* fStr;
  TClonesArray* fTracks;

  hcalAnalysisSimple(const hcalAnalysisSimple&);
  hcalAnalysisSimple operator=(const hcalAnalysisSimple&);

  ClassDef(hcalAnalysisSimple,1)
};

#endif 

