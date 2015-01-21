#ifndef ECALMAXIMUMLOCATOR_H
#define ECALMAXIMUMLOCATOR_H

#include "FairTask.h"

class TClonesArray;
class ecalStructure;
class TClonesArray;

class ecalMaximumLocator : public FairTask
{
public: 
  /** An empty constructor **/
  ecalMaximumLocator();
  ecalMaximumLocator(const char* name, Int_t verbose);
  virtual void Exec(const Option_t* option);
  virtual InitStatus Init();
  TClonesArray* InitPython(ecalStructure* structure);
  virtual void Finish();
  ~ecalMaximumLocator();

  Double_t ECut() const {return fECut;}
  void SetECut(Double_t ecut=0.005) {fECut=ecut;}
private:
  /** Array of found maximums **/
  TClonesArray* fMaximums;
  /** A calorimeter structure **/
  ecalStructure* fStr;
  /** energy cut on energy of maximum**/
  Double_t fECut;
  /** Current event **/
  Int_t fEvent;

  ecalMaximumLocator(const ecalMaximumLocator&);
  ecalMaximumLocator& operator=(const ecalMaximumLocator&);

  ClassDef(ecalMaximumLocator, 1);
};

#endif
