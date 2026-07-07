// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "TTreeGenerator.h"

#include "FairLogger.h"

namespace SHiP {

TTreeGenerator::TTreeGenerator()
    : Generator(),
      fInputFile(nullptr),
      fInputTree(nullptr),
      fTreeName("events"),
      fNEvents(0),
      fCurrentEvent(0),
      fPx(0),
      fPy(0),
      fPz(0),
      fX(0),
      fY(0),
      fZ(0),
      fPdgId(0),
      fWeight(1.0) {}

TTreeGenerator::~TTreeGenerator() {
  if (fInputFile) {
    fInputFile->Close();
    delete fInputFile;
  }
}

Bool_t TTreeGenerator::Init(const char* fileName) { return Init(fileName, 0); }

Bool_t TTreeGenerator::Init(const char* fileName, int startEvent) {
  if (startEvent < 0) {
    LOG(error) << "TTreeGenerator: startEvent must be >= 0, got " << startEvent;
    return kFALSE;
  }

  if (fInputFile) {
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
  }
  fInputTree = nullptr;
  fNEvents = 0;
  fCurrentEvent = 0;

  fInputFile = TFile::Open(fileName, "READ");
  if (!fInputFile) {
    LOG(error) << "TTreeGenerator: Cannot open file " << fileName;
    delete fInputFile;
    fInputFile = nullptr;
    return kFALSE;
  }

  fInputTree = dynamic_cast<TTree*>(fInputFile->Get(fTreeName.Data()));
  if (!fInputTree) {
    LOG(error) << "TTreeGenerator: Cannot find tree " << fTreeName.Data()
               << " in file " << fileName;
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fInputTree = nullptr;
    return kFALSE;
  }

  fNEvents = fInputTree->GetEntries();
  if (startEvent >= fNEvents) {
    LOG(error) << "TTreeGenerator: startEvent " << startEvent
               << " is out of range for " << fNEvents << " entries";
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fInputTree = nullptr;
    fNEvents = 0;
    return kFALSE;
  }
  fCurrentEvent = startEvent;
  LOG(info) << "TTreeGenerator: Found " << fNEvents
            << " events in tree, starting at " << startEvent;

  if (!InitBranches()) {
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fInputTree = nullptr;
    fNEvents = 0;
    fCurrentEvent = 0;
    return kFALSE;
  }

  return kTRUE;
}

Bool_t TTreeGenerator::ReadEvent(FairPrimaryGenerator* primGen) {
  if (!fInputTree || fCurrentEvent >= fNEvents) {
    return kFALSE;
  }
  if (fInputTree->GetEntry(fCurrentEvent) <= 0) {
    LOG(error) << "TTreeGenerator: Failed to read entry " << fCurrentEvent;
    return kFALSE;
  }

  // Position in cm, momentum in GeV/c
  primGen->AddTrack(fPdgId, fPx, fPy, fPz, fX, fY, fZ, -1, true, 0., 0.,
                    fWeight);

  fCurrentEvent++;

  return kTRUE;
}

Bool_t TTreeGenerator::InitBranches() {
  if (!fInputTree) return kFALSE;

  bool ok = true;

  ok &= (fInputTree->SetBranchAddress("px", &fPx) >= 0);
  ok &= (fInputTree->SetBranchAddress("py", &fPy) >= 0);
  ok &= (fInputTree->SetBranchAddress("pz", &fPz) >= 0);

  ok &= (fInputTree->SetBranchAddress("x", &fX) >= 0);
  ok &= (fInputTree->SetBranchAddress("y", &fY) >= 0);
  ok &= (fInputTree->SetBranchAddress("z", &fZ) >= 0);

  ok &= (fInputTree->SetBranchAddress("id", &fPdgId) >= 0);
  ok &= (fInputTree->SetBranchAddress("w", &fWeight) >= 0);

  if (!ok) {
    LOG(error) << "TTreeGenerator: failed to bind one or more branches";
  }

  return ok ? kTRUE : kFALSE;
}

}  // namespace SHiP
