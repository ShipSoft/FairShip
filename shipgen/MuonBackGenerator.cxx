// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include <vector>
#include <string>
#include "MuonBackGenerator.h"

#include <math.h>

#include <algorithm>
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
                               const int firstEvent) {
  LOG(info) << "Opening input file " << fileNames.at(0);
  TFile testFile(fileNames.at(0).c_str());
  auto testKeys = testFile.GetListOfKeys();
  if (testKeys == nullptr) {
    LOG(fatal) << "Error opening the Signal file: " << fileNames.at(0);
  }
  fn = firstEvent;
  fPaintBeam = 5 * cm;  // default value for painting beam
  fSameSeed = 0;
  fPhiRandomize = false;      // default value for phi randomization
  fsmearBeam = 8 * mm;        // default value for smearing beam
  fdownScaleDiMuon = kFALSE;  // only needed for muflux simulation
  if (testKeys->FindObject("pythia8-Geant4")) {
    fTree = new TChain("pythia8-Geant4");
    for (auto& f : fileNames) {
      LOG(info) << "Opening input file " << f;
      fTree->Add(f.c_str());
    }
    fNevents = fTree->GetEntries();
    LOG(info) << "Reading " << fNevents << " entries";
    // count only events with muons
    fTree->SetBranchAddress("id", &id);  // particle id
    fTree->SetBranchAddress("parentid",
                            &parentid);  // parent id, could be different
    fTree->SetBranchAddress("pythiaid",
                            &pythiaid);      // pythiaid original particle
    fTree->SetBranchAddress("ecut", &ecut);  // energy cut used in simulation
    fTree->SetBranchAddress("w", &w);        // weight of event
    //  check if ntuple has information of momentum at origin
    if (fTree->GetListOfLeaves()->GetSize() < 17) {
      fTree->SetBranchAddress(
          "x", &vx);  // position with respect to startOfTarget at -89.27m
      fTree->SetBranchAddress("y", &vy);
      fTree->SetBranchAddress("z", &vz);
      fTree->SetBranchAddress("px", &px);  // momentum
      fTree->SetBranchAddress("py", &py);
      fTree->SetBranchAddress("pz", &pz);
    } else {
      fTree->SetBranchAddress(
          "ox", &vx);  // position with respect to startOfTarget at -50m
      fTree->SetBranchAddress("oy", &vy);
      fTree->SetBranchAddress("oz", &vz);
      fTree->SetBranchAddress("opx", &px);  // momentum
      fTree->SetBranchAddress("opy", &py);
      fTree->SetBranchAddress("opz", &pz);
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
    // Detect format by checking branch name:
    // STL format uses PlaneHAPoint, TClonesArray uses vetoPoint
    TBranch* mcBranch = fTree->GetBranch("MCTrack");
    if (!mcBranch) {
      LOG(fatal) << "MCTrack branch not found in input file";
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
        LOG(fatal) << "Failed to set branch addresses for STL vector format";
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
        LOG(fatal) << "Failed to set branch addresses for TClonesArray format";
      }
      LOG(info) << "Using TClonesArray format (vetoPoint)";
    } else {
      LOG(fatal)
          << "Neither PlaneHAPoint nor vetoPoint branch found in input file";
    }
  }
  return kTRUE;
}

// -----   Default constructor   -------------------------------------------
Bool_t MuonBackGenerator::Init(const char* fileName, const int firstEvent) {
  std::vector<std::string> fileNames = {fileName};
  return Init(fileNames, firstEvent);
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

  while (fn < fNevents) {
    fTree->GetEntry(fn);
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
        LOGF(warn, "No muon found %i", fn - 1);
      }
      if (found) {
        break;
      }
    }
  }
  if (fn == fNevents) {
    LOGF(info, "End of tree reached %i", fNevents);
    return kFALSE;
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
    cpg->AddTrack(static_cast<int>(pythiaid), px, py, pz, vx * 100., vy * 100.,
                  vz * 100., -1., false, e, pythiaid, parentid);
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
