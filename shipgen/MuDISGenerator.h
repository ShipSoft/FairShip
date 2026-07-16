// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_MUDISGENERATOR_H_
#define SHIPGEN_MUDISGENERATOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Generator.h"
#include "TF1.h"
#include "TROOT.h"
#include "TChain.h"
#include "TVector3.h"
#include "vector"

#include "MuDISDefs.h"

using namespace ShipMuDIS;

class FairPrimaryGenerator;

class MuDISGenerator : public SHiP::Generator {
 public:
  /** default constructor **/
  MuDISGenerator();

  /** destructor **/
  ~MuDISGenerator() = default;

  /** public method ReadEvent **/
  using SHiP::Generator::Init;
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  Bool_t Init(const char*, int) override;
  Bool_t Init(const char*) override;
  Bool_t Init(const std::vector<std::string>&, int) override;
  Bool_t Init(const std::vector<std::string>&) override;
  Int_t GetNevents();
  void SetNevents();

 protected:
  FairLogger* fLogger;  //!   don't make it persistent, magic ROOT command
  TChain* fTree;
  int fNevents;
  MuonInBranches finEv;
  int fn;//counter of final output events
  int fnmu;//counter of original input muons
  unsigned fMat;//index of material
  int fnmuDis;//counter of DIS event per input muon per material
  int fnmuDisDau;//counter of daughter particles per input muon per material

  
};
#endif  // SHIPGEN_MUDISGENERATOR_H_
