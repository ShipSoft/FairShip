// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "MuonBackGenerator.h"

#include <algorithm>
#include <cmath>
#include <unordered_map>

#include "BeamSmearingUtils.h"
#include "FairPrimaryGenerator.h"
#include "ShipMCTrack.h"
#include "ShipUnit.h"
#include "TChain.h"
#include "TDatabasePDG.h"  // for TDatabasePDG
#include "TFile.h"
#include "TMCProcess.h"
#include "TMath.h"  // for Sqrt
#include "TROOT.h"
#include "TRandom.h"
#include "TSystem.h"
#include "TVector.h"
#include "TVirtualMC.h"
#include "vetoPoint.h"

using ShipUnit::cm;
using ShipUnit::mm;
// read events from Pythia8/Geant4 base simulation (only target + hadron
// absorber

// -----   Default constructor   -------------------------------------------
MuonBackGenerator::MuonBackGenerator()
    : MCTrack_vec(nullptr), vetoPoints_vec(nullptr), fUseSTL(false) {
  followMuons = true;
}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName) {
  return Init(fileName, 0);
}

Bool_t MuonBackGenerator::Init(const std::vector<std::string>& fileNames) {
  return Init(fileNames, 0);
}

Bool_t MuonBackGenerator::Init(const std::vector<std::string>& fileNames,
                               const int startEvent) {
  if (fileNames.empty()) {
    LOG(error) << "MuonBackGenerator: no input files provided. "
               << "Check the -f/--inputFile argument or input file glob.";
    return kFALSE;
  }
  for (const auto& fileName : fileNames) {
    if (fileName.empty()) {
      LOG(error) << "MuonBackGenerator: received an empty input file name. "
                 << "Check the -f/--inputFile argument.";
      return kFALSE;
    }
  }
  if (startEvent < 0) {
    LOG(error) << "MuonBackGenerator: startEvent must be >= 0, got "
               << startEvent;
    return kFALSE;
  }

  LOG(info) << "Opening input file to find keys " << fileNames.at(0);
  TFile* testFile = TFile::Open(fileNames.at(0).c_str(), "READ");
  auto testKeys = testFile ? testFile->GetListOfKeys() : nullptr;
  if (testKeys == nullptr) {
    delete testFile;
    LOG(error) << "MuonBackGenerator: Error opening input file "
               << fileNames.at(0)
               << ". Check that the path is correct and the file is a readable "
                  "ROOT file.";
    return kFALSE;
  }
  const bool hasPythia8Geant4 =
      testKeys->FindObject("pythia8-Geant4") != nullptr;
  testFile->Close();
  delete testFile;
  fn = startEvent;
  fPaintBeam = 5 * cm;  // default value for painting beam
  fSameSeed = 0;
  fPhiRandomize = false;      // default value for phi randomization
  fsmearBeam = 8 * mm;        // default value for smearing beam
  fdownScaleDiMuon = kFALSE;  // only needed for muflux simulation
  if (hasPythia8Geant4) {
    fTree = new TChain("pythia8-Geant4");
    for (auto& f : fileNames) {
      LOG(info) << "Opening input file " << f;
      fTree->Add(f.c_str());
    }
    fNevents = fTree->GetEntries();
    LOG(info) << "Reading " << fNevents << " entries";
    if (startEvent >= fNevents) {
      LOG(error) << "MuonBackGenerator: startEvent " << startEvent
                 << " is out of range for " << fNevents << " entries";
      return kFALSE;
    }
    // count only events with muons
    bool ok = true;
    ok &= (fTree->SetBranchAddress("id", &id) >= 0);
    ok &= (fTree->SetBranchAddress("parentid", &parentid) >= 0);
    ok &= (fTree->SetBranchAddress("pythiaid", &pythiaid) >= 0);
    ok &= (fTree->SetBranchAddress("ecut", &ecut) >= 0);
    ok &= (fTree->SetBranchAddress("w", &w) >= 0);
    //  check if ntuple has information of momentum at origin
    if (fTree->GetListOfLeaves()->GetSize() < 17) {
      ok &= (fTree->SetBranchAddress("x", &vx) >= 0);
      ok &= (fTree->SetBranchAddress("y", &vy) >= 0);
      ok &= (fTree->SetBranchAddress("z", &vz) >= 0);
      ok &= (fTree->SetBranchAddress("px", &px) >= 0);
      ok &= (fTree->SetBranchAddress("py", &py) >= 0);
      ok &= (fTree->SetBranchAddress("pz", &pz) >= 0);
    } else {
      ok &= (fTree->SetBranchAddress("ox", &vx) >= 0);
      ok &= (fTree->SetBranchAddress("oy", &vy) >= 0);
      ok &= (fTree->SetBranchAddress("oz", &vz) >= 0);
      ok &= (fTree->SetBranchAddress("opx", &px) >= 0);
      ok &= (fTree->SetBranchAddress("opy", &py) >= 0);
      ok &= (fTree->SetBranchAddress("opz", &pz) >= 0);
    }
    if (!ok) {
      LOG(error) << "MuonBackGenerator: failed to bind one or more required "
                    "branches for pythia8-Geant4 input";
      return kFALSE;
    }
  } else {
    id = -1;
    fTree = new TChain("cbmsim");
    for (auto& f : fileNames) {
      LOG(info) << "Opening input file " << f;
      fTree->Add(f.c_str());
    }
    fNevents = fTree->GetEntries();
    LOG(info) << "Reading " << fNevents << " entries";
    if (startEvent >= fNevents) {
      LOG(error) << "MuonBackGenerator: startEvent " << startEvent
                 << " is out of range for " << fNevents << " entries";
      return kFALSE;
    }
    // Detect format by checking branch name:
    // STL format uses PlaneHAPoint, TClonesArray uses vetoPoint
    TBranch* mcBranch = fTree->GetBranch("MCTrack");
    if (!mcBranch) {
      LOG(error) << "MuonBackGenerator: MCTrack branch not found in input file";
      return kFALSE;
    }

    if (fTree->GetBranch("PlaneHAPoint")) {
      // New STL format
      fUseSTL = true;
      MCTrack_vec = nullptr;
      vetoPoints_vec = nullptr;
      auto mcStatus = fTree->SetBranchAddress("MCTrack", &MCTrack_vec);
      auto vetoStatus =
          fTree->SetBranchAddress("PlaneHAPoint", &vetoPoints_vec);
      if (mcStatus < 0 || vetoStatus < 0) {
        LOG(error) << "MuonBackGenerator: Failed to set branch addresses for "
                      "STL vector format";
        return kFALSE;
      }
      LOG(info) << "Using STL vector format (PlaneHAPoint)";
    } else if (fTree->GetBranch("vetoPoint")) {
      // Old TClonesArray format
      fUseSTL = false;
      MCTrack = new TClonesArray("ShipMCTrack");
      vetoPoints = new TClonesArray("vetoPoint");
      auto mcStatus = fTree->SetBranchAddress("MCTrack", &MCTrack);
      auto vetoStatus = fTree->SetBranchAddress("vetoPoint", &vetoPoints);
      if (mcStatus < 0 || vetoStatus < 0) {
        LOG(error) << "MuonBackGenerator: Failed to set branch addresses for "
                      "TClonesArray format";
        return kFALSE;
      }
      LOG(info) << "Using TClonesArray format (vetoPoint)";
    } else {
      LOG(error) << "MuonBackGenerator: Neither PlaneHAPoint nor vetoPoint "
                    "branch found in input file";
      return kFALSE;
    }
  }
  return kTRUE;
}

// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName, const int startEvent) {
  std::vector<std::string> fileNames = {fileName};
  return Init(fileNames, startEvent);
}
// -----   Destructor   ----------------------------------------------------
MuonBackGenerator::~MuonBackGenerator() {
  if (!fUseSTL) {
    delete MCTrack;
    delete vetoPoints;
  }
}
// -------------------------------------------------------------------------
Bool_t MuonBackGenerator::checkDiMuon(Int_t muIndex) {
  ShipMCTrack* mu = fUseSTL ? &(*MCTrack_vec)[muIndex]
                            : dynamic_cast<ShipMCTrack*>(MCTrack->At(muIndex));
  TString pName = mu->GetProcName();
  if (strncmp("Hadronic inelastic", pName.Data(), 18) == 0 ||
      strncmp("Positron annihilation", pName.Data(), 21) == 0 ||
      strncmp("Lepton pair production", pName.Data(), 22) == 0) {
    return true;
  }
  Int_t motherId = mu->GetMotherId();
  if (motherId < 0) {
    return false;
  }
  ShipMCTrack* mother = fUseSTL
                            ? &(*MCTrack_vec)[motherId]
                            : dynamic_cast<ShipMCTrack*>(MCTrack->At(motherId));
  Int_t Pcode = TMath::Abs(mother->GetPdgCode());
  return (Pcode == 221 || Pcode == 223 || Pcode == 333 || Pcode == 113 ||
          Pcode == 331);
}

// -----   Passing the event   ---------------------------------------------
Bool_t MuonBackGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  auto* pdgBase = TDatabasePDG::Instance();
  Double_t mass = 0., e = 0., tof = 0.;
  std::unordered_map<int, int> muList;
  std::unordered_map<int, std::vector<int>> moList;

  // Helper lambdas to abstract STL vs TClonesArray access
  auto getVetoSize = [this]() -> int {
    return fUseSTL ? vetoPoints_vec->size() : vetoPoints->GetEntries();
  };
  auto getVetoPoint = [this](int i) -> vetoPoint* {
    return fUseSTL ? &(*vetoPoints_vec)[i]
                   : dynamic_cast<vetoPoint*>(vetoPoints->At(i));
  };
  auto getMCTrack = [this](int i) -> ShipMCTrack* {
    return fUseSTL ? &(*MCTrack_vec)[i]
                   : dynamic_cast<ShipMCTrack*>(MCTrack->At(i));
  };
  auto getMCTrackSize = [this]() -> int {
    return fUseSTL ? MCTrack_vec->size() : MCTrack->GetEntries();
  };

  bool found_muon = false;
  while (fn < fNevents) {
    fTree->GetEntry(fn);
    IncrementCounter("scanned_entries");
    muList.clear();
    moList.clear();
    fn++;
    if (fn % 100000 == 0) {
      LOGF(info, "Reading event %i", fn);
    }
    // test if we have a muon, don't look at neutrinos:
    if (TMath::Abs(static_cast<int>(id)) == 13) {
      mass = pdgBase->GetParticle(id)->Mass();
      e = TMath::Sqrt(px * px + py * py + pz * pz + mass * mass);
      tof = 0;
      found_muon = true;
      break;
    }
    if (id == -1) {  // use tree as input file
      Bool_t found = false;
      for (int i = 0; i < getVetoSize(); i++) {
        auto* v = getVetoPoint(i);
        Int_t abspid = TMath::Abs(v->PdgCode());
        if (abspid == 13 || (!followMuons && abspid != 12 && abspid != 14)) {
          found = true;
          Int_t muIndex = v->GetTrackID();
          if (!fdownScaleDiMuon) {
            muList.insert({muIndex, i});
          } else if (abspid == 13) {
            if (checkDiMuon(muIndex)) {
              moList[getMCTrack(muIndex)->GetMotherId()].push_back(i);
            } else {
              muList.insert({muIndex, i});
            }
          }
        }
      }
      // reject muon if comes from boosted channel

      for (auto it = moList.begin(); it != moList.end(); it++) {
        if (gRandom->Uniform(0., 1.) > 0.99) {
          std::vector<int> list = it->second;
          for (unsigned i = 0; i < list.size(); i++) {
            auto* v = getVetoPoint(list.at(i));
            Int_t muIndex = v->GetTrackID();
            muList.insert({muIndex, i});
          }
        }
      }
      if (!found) {
        LOGF(debug, "No muon found %i", fn - 1);
      }
      if (found) {
        IncrementCounter("accepted_entries");
        IncrementCounter("selected_muons", muList.size());
        found_muon = true;
        break;
      }
    }
  }
  if (fn >= fNevents && !found_muon) {
    LOGF(info, "End of tree reached %i", fNevents);
    gMC->StopRun();
    return kTRUE;
  }
  if (fSameSeed) {
    Int_t theSeed = fn + fSameSeed * fNevents;
    LOGF(debug, "Seed: %d", theSeed);
    gRandom->SetSeed(theSeed);
  }
  auto [dx, dy] = CalculateBeamOffset(fsmearBeam, fPaintBeam);
  if (id == -1) {
    for (int i = 0; i < getMCTrackSize(); i++) {
      auto* track = getMCTrack(i);
      Int_t abspid = TMath::Abs(track->GetPdgCode());
      px = track->GetPx();
      py = track->GetPy();
      pz = track->GetPz();
      if (fPhiRandomize) {
        double phi_random = gRandom->Uniform(0., 2 * TMath::Pi());
        Double_t pt = track->GetPt();
        px = pt * TMath::Cos(phi_random);
        py = pt * TMath::Sin(phi_random);
      }
      vx = track->GetStartX() + dx;
      vy = track->GetStartY() + dy;
      vz = track->GetStartZ();
      tof = track->GetStartT() / 1E9;  // convert back from ns to sec;
      e = track->GetEnergy();
      Bool_t wanttracking = false;  // only transport muons
      for (std::pair<int, int> element : muList) {
        if (element.first == i) {
          wanttracking = true;
          if (!followMuons) {
            auto* v = getVetoPoint(element.second);
            TVector3 lpv = v->LastPoint();
            TVector3 lmv = v->LastMom();
            if (abspid == 22) {
              e = lmv.Mag();
            } else {
              e = TMath::Sqrt(lmv.Mag2() +
                              (track->GetMass()) * (track->GetMass()));
            }
            px = lmv[0];
            py = lmv[1];
            pz = lmv[2];
            vx = lpv[0];
            vy = lpv[1];
            vz = lpv[2];
            tof = v->GetTime() / 1E9;  // convert back from ns to sec
          }
          break;
        }
      }
      IncrementCounter("transported_tracks");
      cpg->AddTrack(track->GetPdgCode(), px, py, pz, vx, vy, vz,
                    track->GetMotherId(), wanttracking, e, tof,
                    track->GetWeight(), (TMCProcess)track->GetProcID());
    }
  } else {
    vx += dx / 100.;
    vy += dy / 100.;
    if (fPhiRandomize) {
      double phi_random = gRandom->Uniform(0., 2 * TMath::Pi());
      Double_t pt = TMath::Sqrt(px * px + py * py);
      px = pt * TMath::Cos(phi_random);
      py = pt * TMath::Sin(phi_random);
    }
    IncrementCounter("accepted_entries");
    IncrementCounter("selected_muons");
    cpg->AddTrack(static_cast<int>(pythiaid), px, py, pz, vx * 100., vy * 100.,
                  vz * 100., -1., false, e, pythiaid, parentid);
    IncrementCounter("transported_tracks", 2);
    cpg->AddTrack(static_cast<int>(id), px, py, pz, vx * 100., vy * 100.,
                  vz * 100., -1., true, e, tof, w);
  }
  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t MuonBackGenerator::GetNevents() { return fNevents; }
void MuonBackGenerator::CloseFile() {
  fInputFile->Close();
  fInputFile->Delete();
  delete fInputFile;
}
