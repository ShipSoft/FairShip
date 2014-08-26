#ifndef ECALANALYSISCALIB_H
#define ECALANALYSISCALIB_H

#include "FairTask.h"

#include "TString.h"

#include <list>

class TTree;
class ecalStructure;
class TClonesArray;

class ecalAnalysisSimple : public FairTask
{
public:
  ecalAnalysisSimple(const char* name, const Int_t iVerbose);

  /** Default constructor **/
  ecalAnalysisSimple();

  /** Initing routine **/
  virtual InitStatus Init();

  /** Loop procedure **/
  virtual void Exec(Option_t* option);

  /** Finishing routine **/
  virtual void Finish();

  /** Destructor **/
  virtual ~ecalAnalysisSimple() {};

private:
  TTree* fTree;
  Double_t fX;
  Double_t fY;
  Double_t fCX;
  Double_t fCY;
  Double_t fP;
  Double_t fCE;
  Double_t fOE;
  Double_t fPX;
  Double_t fPY;
  Double_t fPZ;
  Int_t fEv;
  Int_t fCellNum;
  Int_t fADC;
  void InitTree();
  ecalStructure* fStr;
  TClonesArray* fTracks;

  ecalAnalysisSimple(const ecalAnalysisSimple&);
  ecalAnalysisSimple operator=(const ecalAnalysisSimple&);

  ClassDef(ecalAnalysisSimple,1)
};

#endif 

