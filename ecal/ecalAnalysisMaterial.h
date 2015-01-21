#ifndef ECALANALYSISMATERIAL_H
#define ECALANALYSISMATERIAL_H

#include "FairTask.h"

#include "TString.h"

#include <list>

class TTree;
class TClonesArray;


class ecalAnalysisMaterial : public FairTask
{
public:
  ecalAnalysisMaterial(const char* name, const Int_t iVerbose=0);
public:
  /** Default constructor **/
  ecalAnalysisMaterial();

  /** Initing routine **/
  virtual InitStatus Init();

  /** Loop procedure **/
  virtual void Exec(Option_t* option);

  /** Finishing routine **/
  virtual void Finish();

  /** Destructor **/
  virtual ~ecalAnalysisMaterial() {};
private:
  /** Initialize a tree **/
  void InitTree();
  /** Out tree **/
  TTree* fTree;			//!

  /** Event number **/
  Int_t fEvent;
  /** Information particle **/
  Double_t fX;
  Double_t fY;
  Double_t fZ;
  Double_t fX0;
  Double_t fX0z[400];
  Double_t fIntL;


  /** MC tracks array **/
  TClonesArray* fMC;		//!
  /** Array of radlen points**/
  TClonesArray* fRadLen;	//!

  ecalAnalysisMaterial(const ecalAnalysisMaterial&);
  ecalAnalysisMaterial& operator=(const ecalAnalysisMaterial&);

  ClassDef(ecalAnalysisMaterial,1)
};

#endif 

