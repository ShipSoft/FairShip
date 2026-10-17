// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_NEWMUDISGENERATOR_H_
#define NEWMUONDIS_NEWMUDISGENERATOR_H_

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Generator.h"
#include "MuDISDefs.h"
#include "TChain.h"

class FairPrimaryGenerator;

class NewMuDISGenerator : public SHiP::Generator {
 public:
  /** default constructor **/
  NewMuDISGenerator();

  /** public method ReadEvent **/
  using SHiP::Generator::Init;
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  // startEvent is a zero-based muon entry in the input MuonDIS tree/chain.
  Bool_t Init(const char*, int) override;
  Bool_t Init(const char*) override;
  Bool_t Init(const std::vector<std::string>&, int) override;
  Bool_t Init(const std::vector<std::string>&) override;
  int GetNevents();  // DIS interactions in the selected input muon range
  // Material labels in replay order, exposed in a PyROOT-compatible container.
  static std::vector<std::string> GetMaterialNames();
  // Limit input muons from startEvent (-1: all, 0: none), also before Init.
  // GetNevents() is -1 if counting/validation fails.
  void SetNevents(int nMuons = -1);
  // Attach to an empty output tree before replay; this generator must outlive
  // it.
  bool RegisterOutputBranches(TTree* tree);
  // MatType value for the last successful ReadEvent, or -1 after Init/failure.
  int GetMaterial() const { return fDISMaterial; }

 protected:
  std::unique_ptr<TChain> fTree;
  int fNevents = -1;
  int fStartEvent = 0;
  int fMaxMuons = -1;
  std::int64_t fEndEvent = 0;
  bool fEntryLoaded = false;
  bool ValidateEntry(std::int64_t entry) const;
  void ResetOutputBranches();
  ShipMuDIS::MuonInBranches finEv;
  int fn = 0;                  // counter of final output events
  std::int64_t fnmu = 0;       // counter of original input muons
  unsigned fMat = 0;           // index of material
  int fDISMaterial = -1;       // material of the current output DIS event
  std::string fMaterialLabel;  // material string for output branch
  int fMuonEntry = -1;         // original input muon index for output branch
  int fDISIndex = -1;          // original DIS index for output branch
  double fDISXsec = -1.;       // cross section of the DIS event
  double fPythiaP = -1.;  // momentum of the muon used to generate the DIS event
  std::vector<int> fNGenerated;  // initial count of generated DIS events
  int fnmuDis = 0;  // counter of DIS event per input muon per material
  std::size_t fnmuDisDau = 0;  // daughter offset per input muon per material
};
#endif  // NEWMUONDIS_NEWMUDISGENERATOR_H_
