// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_TPYTHIA6GENERATOR_H_
#define SHIPGEN_TPYTHIA6GENERATOR_H_

#include <utility>

#include "FairLogger.h"
#include "Generator.h"
#include "TPythia6.h"
#include "TPythia6Calls.h"
#include "TROOT.h"
#include "TString.h"

class FairPrimaryGenerator;

class tPythia6Generator : public SHiP::Generator {
 public:
  /** default constructor **/
  tPythia6Generator();

  /** destructor **/
  ~tPythia6Generator() override;

  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*) override;

  using SHiP::Generator::Init;
  Bool_t Init() override;
  Bool_t Init(const char* inFile) override { return Init(inFile, 0); };
  Bool_t Init(const char* inFile, int startEvent) override {
    LOG(warning) << "Init with files not implemented for tPythia6Generator. "
                    "Using default Init() instead";
    return Init();
  };

  void SetMom(Double_t mom) { fMom = mom; };
  void SetTarget(TString Type, TString Target) {
    fType = std::move(Type);
    fTarget = std::move(Target);
  };
  void UseDeepCopy() { fDeepCopy = kTRUE; };
  double getPyint5_XSEC(int i, int j) {
    return fPythia->GetPyint5()->XSEC[i][j];
  };
  double getPyint5_NGEN(int i, int j) {
    return fPythia->GetPyint5()->NGEN[i][j];
  };
  int getPyint5_NGENPD() { return fPythia->GetPyint5()->NGENPD; };

 private:
  TPythia6* fPythia;  //!

 protected:
  Double_t fMom;     // proton momentum
  Bool_t fDeepCopy;  // copy complete pythia event
  Bool_t fPionKaonDecay;
  TString fType;  // muon proton scattering
  TString fTarget;
};

#endif  // SHIPGEN_TPYTHIA6GENERATOR_H_ /* !PNDP6GENERATOR_H */
