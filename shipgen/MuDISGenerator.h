// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_MUDISGENERATOR_H_
#define SHIPGEN_MUDISGENERATOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Generator.h"
#include "TClonesArray.h"
#include "TF1.h"  // for TF1
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TVector3.h"
#include "vector"

#include "MuDISDefs.h"

class FairPrimaryGenerator;

class MuDISGenerator : public SHiP::Generator {
 public:
  /** default constructor **/
  MuDISGenerator();

  /** destructor **/
  ~MuDISGenerator() override;

  /** public method ReadEvent **/
  using SHiP::Generator::Init;
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  Bool_t Init(const char*) override;
  Int_t GetNevents();

 protected:
  FairLogger* fLogger;  //!   don't make it persistent, magic ROOT command
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  MuonInBranches finEv;
  int fnmu;//counter of original input muons
  int fnmuDis;//counter of DIS event per input muon
  int fnmuDisDau;//counter of daughter particles per input muon

  
};
#endif  // SHIPGEN_MUDISGENERATOR_H_
