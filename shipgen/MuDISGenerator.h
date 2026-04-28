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
  Bool_t Init(const char*, int) override;
  Bool_t Init(const char*) override;
  Int_t GetNevents();

  void SetPositions(Double_t z_start, Double_t z_end) {
    startZ = z_start;
    endZ = z_end;
  }
  Long64_t GetGeneratedEvents() const { return fGeneratedEvents; }
  Long64_t GetInteractionSamplingTrials() const { return fInteractionSamplingTrials; }
  Long64_t GetDISParticlesStored() const { return fDISParticlesStored; }
  Long64_t GetSoftParticlesStored() const { return fSoftParticlesStored; }
  Long64_t GetSoftParticlesSkipped() const { return fSoftParticlesSkipped; }

 protected:
  Double_t startZ, endZ;
  TClonesArray* iMuon;
  TClonesArray* dPart;
  TClonesArray* dPartSoft;
  FairLogger* fLogger;  //!   don't make it persistent, magic ROOT command
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  bool fFirst;
  Long64_t fGeneratedEvents;
  Long64_t fInteractionSamplingTrials;
  Long64_t fDISParticlesStored;
  Long64_t fSoftParticlesStored;
  Long64_t fSoftParticlesSkipped;
};
#endif  // SHIPGEN_MUDISGENERATOR_H_
