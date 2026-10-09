// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "NewMuDISGenerator.h"

#include <algorithm>
#include <limits>

#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "TFile.h"

using namespace ShipMuDIS;

NewMuDISGenerator::NewMuDISGenerator() { ResetOutputBranches(); }

std::vector<std::string> NewMuDISGenerator::GetMaterialNames() {
  return {MatTypeStr.begin(), MatTypeStr.end()};
}

Bool_t NewMuDISGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}

Bool_t NewMuDISGenerator::Init(const std::vector<std::string>& fileNames) {
  return Init(fileNames, 0);
}

Bool_t NewMuDISGenerator::Init(const std::vector<std::string>& fileNames,
                               const int startEvent) {
  ResetOutputBranches();
  fNevents = -1;
  fEntryLoaded = false;
  if (startEvent < 0) {
    LOG(error) << "NewMuDISGenerator: startEvent must be nonnegative";
    return false;
  }
  if (fileNames.empty()) {
    LOG(error) << "NewMuDISGenerator: no input files provided. "
               << "Check the -f/--inputFile argument or input file glob.";
    return false;
  }
  for (const auto& fileName : fileNames) {
    if (fileName.empty()) {
      LOG(error) << "NewMuDISGenerator: received an empty input file name. "
                 << "Check the -f/--inputFile argument.";
      return false;
    }
  }

  LOG(info) << "Opening input file to find keys " << fileNames.at(0);
  std::unique_ptr<TFile> testFile(TFile::Open(fileNames.at(0).c_str(), "READ"));
  auto testKeys = testFile ? testFile->GetListOfKeys() : nullptr;
  if (testKeys == nullptr) {
    LOG(error) << "NewMuDISGenerator: Error opening input file "
               << fileNames.at(0)
               << ". Check that the path is correct and the file is a readable "
                  "ROOT file.";
    return false;
  }
  const bool hasDIStree = testKeys->FindObject("MuonDIS") != nullptr;
  testFile->Close();

  if (hasDIStree) {
    fTree = std::make_unique<TChain>("MuonDIS");
    for (auto& f : fileNames) {
      LOG(info) << "Opening input file " << f;
      fTree->Add(f.c_str());
    }
    const std::int64_t treeEvts = fTree->GetEntries();
    LOG(info) << "Reading " << treeEvts << " entries.";
    if (startEvent > treeEvts) {
      LOG(error) << "NewMuDISGenerator: startEvent " << startEvent
                 << " exceeds the number of input muon entries " << treeEvts;
      return false;
    }
    fStartEvent = startEvent;
    fn = 0;
    fnmu = startEvent;
    fMat = 0;
    fnmuDis = 0;
    fnmuDisDau = 0;

    bool ok = finEv.Setup(fTree.get());

    if (!ok) {
      LOG(error)
          << "NewMuDISGenerator: failed to bind one or more required branches";
      return false;
    }
    SetNevents(fMaxMuons);
    if (fNevents < 0) return false;
    LOG(info) << "NewMuDISGenerator: Initialization successful.";
    return true;
  }
  return false;
}

// -----   Default constructor   -------------------------------------------
Bool_t NewMuDISGenerator::Init(const char* fileName, const int startEvent) {
  std::vector<std::string> fileNames = {fileName};
  return Init(fileNames, startEvent);
}

// -----   Passing the event   ---------------------------------------------
Bool_t NewMuDISGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  ResetOutputBranches();
  if (fn >= fNevents) {
    LOG(info) << " Reached total number of DIS events: counter " << fn
              << " nTot=" << fNevents;
    return false;
  }
  LOG(debug) << " - Processing input muon " << fnmu << " fMat " << fMat
             << " fnmuDis " << fnmuDis << " fnmuDisDau " << fnmuDisDau;

  if (!fEntryLoaded) {
    if (!finEv.PrepareEntry(fTree.get(), fnmu) || fTree->GetEntry(fnmu) <= 0) {
      LOG(error) << " Error reading event " << fnmu;
      fNevents = -1;
      return false;
    } else {
      LOG(debug) << " Updated tree entry: " << fnmu;
    }
    if (!ValidateEntry(fnmu)) {
      fNevents = -1;
      return false;
    }
    fEntryLoaded = true;
  }

  // access the different materials in turn
  // accessing by reference leads to sometimes vectors inside branch being reset
  MuonDISInBranches* lBr = &finEv.br[fMat];
  LOG(debug) << "Initial branch: " << lBr->Print(fn, MatTypeStr[fMat]);
  int nDIS = lBr->nDISevts;
  LOG(debug) << " nDIS " << nDIS << " DISparticles size "
             << (*lBr->DISparticles).size() << " fMat " << fMat
             << " local evtNumber " << fn;

  // Counts describe the interactions actually stored, including after
  // filtering. Advance only before producing an event: a successful final event
  // must not fail just because there is no following input muon.
  while (fnmuDis >= nDIS) {
    fMat++;
    fnmuDis = 0;
    fnmuDisDau = 0;
    LOG(debug) << " -- switching material" << fMat;
    if (fMat >= nMats) {
      fMat = 0;
      fnmu++;
      LOG(debug) << " -- switching input muon " << fnmu;
      LOG(debug) << " - Processing input muon " << fnmu << " fMat " << fMat
                 << " fnmuDis " << fnmuDis << " fnmuDisDau " << fnmuDisDau;
      if (fnmu >= fEndEvent || !finEv.PrepareEntry(fTree.get(), fnmu) ||
          fTree->GetEntry(fnmu) <= 0) {
        LOG(error) << " Error reading event " << fnmu;
        fNevents = -1;
        return false;
      } else {
        LOG(debug) << " Updated tree entry: " << fnmu;
      }
      if (!ValidateEntry(fnmu)) {
        fNevents = -1;
        return false;
      }
    }
    lBr = &finEv.br[fMat];
    LOG(debug) << "Updating branch: " << lBr->Print(fn, MatTypeStr[fMat]);
    nDIS = lBr->nDISevts;
  }

  if (fnmu % 10 == 0 && fnmuDis == 0) {
    LOG(info) << "Info NewMuDISGenerator: NewMuDIS original muon event #"
              << fnmu << " material " << fMat << " final event #" << fn;
  }

  if (nDIS > 0) {  // if fMat branch has elements
    if (fnmu > std::numeric_limits<int>::max()) {
      LOG(error) << "NewMuDISGenerator: input muon entry exceeds int range";
      fNevents = -1;
      return false;
    }
    if (fnmuDis < 0 || !lBr->nDISdau || !lBr->DISparticles || !lBr->DISvx ||
        !lBr->DISvy || !lBr->DISvz || !lBr->DISvt ||
        static_cast<std::size_t>(fnmuDis) >= lBr->nDISdau->size() ||
        static_cast<std::size_t>(fnmuDis) >= lBr->DISvx->size() ||
        static_cast<std::size_t>(fnmuDis) >= lBr->DISvy->size() ||
        static_cast<std::size_t>(fnmuDis) >= lBr->DISvz->size() ||
        static_cast<std::size_t>(fnmuDis) >= lBr->DISvt->size()) {
      LOG(error) << "NewMuDISGenerator: invalid DIS index " << fnmuDis
                 << " in input muon " << fnmu << " material " << fMat;
      fNevents = -1;
      return false;
    }
    const int nDaughters = (*lBr->nDISdau)[fnmuDis];
    const auto nDISparts = lBr->DISparticles->size();
    if (nDaughters < 0 || fnmuDisDau > nDISparts ||
        static_cast<std::size_t>(nDaughters) > nDISparts - fnmuDisDau) {
      LOG(error) << "NewMuDISGenerator: invalid daughter range at offset "
                 << fnmuDisDau << " with " << nDaughters << " daughters in "
                 << nDISparts << " DIS particles for input muon " << fnmu
                 << " material " << fMat << " DIS index " << fnmuDis;
      fNevents = -1;
      return false;
    }
    // add also soft tracks up to z_interaction
    bool first = true;
    int idxMum = -1;
    for (auto&& mcTrk : *(finEv.mcTrks)) {
      ShipMCTrack& softP = static_cast<ShipMCTrack&>(mcTrk);
      // first particle is the original muon
      if (first) {
        cpg->AddTrack(softP.GetPdgCode(), softP.GetPx(), softP.GetPy(),
                      softP.GetPz(), softP.GetStartX(), softP.GetStartY(),
                      softP.GetStartZ(), idxMum, false, softP.GetEnergy(),
                      softP.GetStartT() / 1E9, softP.GetWeight());
        // passed the first track, we want to track the soft particles and they
        // all stem from first one.
        first = false;
        idxMum = 0;
      } else if (softP.GetStartZ() <= (*lBr->DISvz)[fnmuDis]) {
        bool wantTracking = softP.GetStartZ() < 12000;
        cpg->AddTrack(softP.GetPdgCode(), softP.GetPx(), softP.GetPy(),
                      softP.GetPz(), softP.GetStartX(), softP.GetStartY(),
                      softP.GetStartZ(), idxMum, wantTracking,
                      softP.GetEnergy(), softP.GetStartT() / 1E9,
                      softP.GetWeight());
      }
    }
    LOG(debug) << " --- Processing dis muon " << fnmuDis << " with "
               << nDaughters << " daughters and " << nDISparts
               << " total DIS particles";
    LOG(debug) << " ---- index dau start " << fnmuDisDau;
    // access the independent DIS events
    for (int iD(0); iD < nDaughters; ++iD) {
      DISparticle& lDau = (*lBr->DISparticles)[fnmuDisDau + iD];
      cpg->AddTrack(lDau.pid, lDau.px, lDau.py, lDau.pz, (*lBr->DISvx)[fnmuDis],
                    (*lBr->DISvy)[fnmuDis], (*lBr->DISvz)[fnmuDis], 0, true,
                    lDau.E, (*lBr->DISvt)[fnmuDis] / 1E9, lBr->wDIS);
    }
    fDISMaterial = static_cast<int>(fMat);
    fMaterialLabel = MatTypeStr[fMat];
    fMuonEntry = static_cast<int>(fnmu);
    fDISIndex = fnmuDis;
    // DISxsec is not reliable yet; retain the -1 placeholder.
    fPythiaP = lBr->pPythia;
    for (unsigned material = 0; material < nMats; ++material) {
      fNGenerated[material] = finEv.br[material].nDISevtsGenerated;
    }
    fnmuDisDau += nDaughters;
    LOG(debug) << " ---- index dau end " << fnmuDisDau;
    fnmuDis++;
    LOG(debug) << " --- increment DIS event " << fnmuDis;
    fn++;
  }  // if fMat branch has elements
  else {
    LOG(error) << " Failed to process input muon " << fnmu << " fMat " << fMat
               << " fnmuDis " << fnmuDis << " fnmuDisDau " << fnmuDisDau
               << " local event " << fn;
    return false;
  }

  if (fn == fNevents) {
    LOG(info) << "-- Reached total number of DIS events: counter " << fn
              << " nTot=" << fNevents;
  }

  return true;
}

// -------------------------------------------------------------------------
int NewMuDISGenerator::GetNevents() { return fNevents; }

bool NewMuDISGenerator::RegisterOutputBranches(TTree* tree) {
  if (!tree || tree->GetEntries() != 0) {
    LOG(error) << "NewMuDISGenerator: output branches require an empty tree";
    return false;
  }
  for (const auto* name : {"muDIS_material", "muDIS_muEntry", "muDIS_disIndex",
                           "muDIS_xsec", "muDIS_pPythia", "muDIS_nGenerated"}) {
    if (tree->GetBranch(name)) {
      LOG(error) << "NewMuDISGenerator: output branch already exists: " << name;
      return false;
    }
  }
  return tree->Branch("muDIS_material", &fMaterialLabel) &&
         tree->Branch("muDIS_muEntry", &fMuonEntry, "muDIS_muEntry/I") &&
         tree->Branch("muDIS_disIndex", &fDISIndex, "muDIS_disIndex/I") &&
         tree->Branch("muDIS_xsec", &fDISXsec, "muDIS_xsec/D") &&
         tree->Branch("muDIS_pPythia", &fPythiaP, "muDIS_pPythia/D") &&
         tree->Branch("muDIS_nGenerated", &fNGenerated);
}

void NewMuDISGenerator::ResetOutputBranches() {
  fDISMaterial = -1;
  fMaterialLabel = "";
  fMuonEntry = -1;
  fDISIndex = -1;
  fDISXsec = -1.;
  fPythiaP = -1.;
  fNGenerated.assign(nMats, -1);
}

bool NewMuDISGenerator::ValidateEntry(std::int64_t entry) const {
  if (!finEv.mcTrks || finEv.mcTrks->empty()) {
    LOG(error) << "NewMuDISGenerator: missing muon tracks in entry " << entry;
    return false;
  }
  for (unsigned material = 0; material < nMats; ++material) {
    if (!finEv.br[material].IsValid()) {
      LOG(error) << "NewMuDISGenerator: inconsistent DIS vectors in entry "
                 << entry << " material " << MatTypeStr[material];
      return false;
    }
  }
  return true;
}

void NewMuDISGenerator::SetNevents(int nMuons) {
  fMaxMuons = nMuons;
  fNevents = -1;
  // Counting reads the tree; reload the current muon before replaying it.
  fEntryLoaded = false;
  if (nMuons < -1) {
    LOG(error)
        << "NewMuDISGenerator: input muon limit must be -1 or nonnegative";
    return;
  }
  if (!fTree) return;
  fEndEvent = nMuons < 0
                  ? fTree->GetEntries()
                  : std::min<std::int64_t>(std::int64_t{fStartEvent} + nMuons,
                                           fTree->GetEntries());
  int total = 0;
  for (std::int64_t iEv = fStartEvent; iEv < fEndEvent; ++iEv) {
    if (!finEv.PrepareEntry(fTree.get(), iEv) || fTree->GetEntry(iEv) <= 0 ||
        !ValidateEntry(iEv)) {
      LOG(error) << "NewMuDISGenerator: error counting input muon " << iEv;
      return;
    }
    for (const auto& br : finEv.br) {
      if (br.nDISevts > std::numeric_limits<int>::max() - total) {
        LOG(error) << "NewMuDISGenerator: DIS event count exceeds int range";
        return;
      }
      total += br.nDISevts;
    }
  }
  fNevents = total;
}
