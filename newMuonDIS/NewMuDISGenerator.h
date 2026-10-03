// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPMuDIS_NEWMUDISGENERATOR_H_
#define SHIPMuDIS_NEWMUDISGENERATOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Generator.h"
#include "MuDISDefs.h"
#include "TChain.h"
#include "TF1.h"
#include "TROOT.h"
#include "TVector3.h"
#include "vector"

class FairPrimaryGenerator;

class NewMuDISGenerator : public SHiP::Generator {
 public:
  /** default constructor **/
  NewMuDISGenerator();

  /** destructor **/
  ~NewMuDISGenerator() override { delete fTree; }

  /** public method ReadEvent **/
  using SHiP::Generator::Init;
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  // startEvent is a zero-based muon entry in the input MuonDIS tree/chain.
  Bool_t Init(const char*, int) override;
  Bool_t Init(const char*) override;
  Bool_t Init(const std::vector<std::string>&, int) override;
  Bool_t Init(const std::vector<std::string>&) override;
  Int_t GetNevents();  // DIS interactions in the selected input muon range
  // Limit input muons from startEvent (-1: all, 0: none), also before Init.
  // GetNevents() is -1 if counting/validation fails.
  void SetNevents(int nMuons = -1);

 protected:
  FairLogger* fLogger;
  TChain* fTree;
  int fNevents;
  int fStartEvent = 0;
  int fMaxMuons = -1;
  Long64_t fEndEvent = 0;
  bool fEntryLoaded = false;
  bool ValidateEntry(Long64_t entry) const;
  ShipMuDIS::MuonInBranches finEv;
  int fn;          // counter of final output events
  Long64_t fnmu;   // counter of original input muons
  unsigned fMat;   // index of material
  int fnmuDis;     // counter of DIS event per input muon per material
  std::size_t fnmuDisDau;  // daughter offset per input muon per material
};
#endif  // SHIPMuDIS_NEWMUDISGENERATOR_H_
