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
  fInputFile = TFile::Open(fileName, "READ");
  if (!fInputFile || fInputFile->IsZombie()) {
    LOG(ERROR) << "TTreeGenerator: Cannot open file " << fileName;
    return kFALSE;
  }

  fInputTree = dynamic_cast<TTree*>(fInputFile->Get(fTreeName.Data()));
  if (!fInputTree) {
    LOG(ERROR) << "TTreeGenerator: Cannot find tree " << fTreeName.Data()
               << " in file " << fileName;
    return kFALSE;
  }

  fNEvents = fInputTree->GetEntries();
  fCurrentEvent = startEvent;
  LOG(INFO) << "TTreeGenerator: Found " << fNEvents
            << " events in tree, starting at " << startEvent;

  InitBranches();

  return kTRUE;
}

Bool_t TTreeGenerator::ReadEvent(FairPrimaryGenerator* primGen) {
  if (!fInputTree || fCurrentEvent >= fNEvents) {
    return kFALSE;
  }

  fInputTree->GetEntry(fCurrentEvent);

  // Position in cm, momentum in GeV/c
  primGen->AddTrack(fPdgId, fPx, fPy, fPz, fX, fY, fZ, -1, true, 0., 0.,
                    fWeight);

  fCurrentEvent++;

  return kTRUE;
}

void TTreeGenerator::InitBranches() {
  if (!fInputTree) return;

  fInputTree->SetBranchAddress("px", &fPx);
  fInputTree->SetBranchAddress("py", &fPy);
  fInputTree->SetBranchAddress("pz", &fPz);
  fInputTree->SetBranchAddress("x", &fX);
  fInputTree->SetBranchAddress("y", &fY);
  fInputTree->SetBranchAddress("z", &fZ);
  fInputTree->SetBranchAddress("id", &fPdgId);
  fInputTree->SetBranchAddress("w", &fWeight);
}

}  // namespace SHiP
