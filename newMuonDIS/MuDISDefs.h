// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUDISDEFS_H_
#define NEWMUONDIS_MUDISDEFS_H_

#include <array>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>

#include "DISparticle.h"
#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "ShipMCTrack.h"
#include "TChain.h"  // for TTree
#include "TTree.h"   // for TTree
#include "TimeDetPoint.h"
#include "UpstreamTaggerPoint.h"
#include "strawtubesPoint.h"
#include "vetoPoint.h"

namespace ShipMuDIS {
static const unsigned nMats = 10;

enum MatType {
  MS = 0,
  UBT = 1,
  SBTsens = 2,
  SBTfr = 3,
  SSTsens = 4,
  SSTfr = 5,
  HE = 6,
  AIR = 7,
  HeBalloon = 8,
  REST = 9
};

inline const std::array<std::string, nMats> MatTypeStr = {
    "MS",    "UBT", "SBTsens", "SBTfr",     "SSTsens",
    "SSTfr", "HE",  "AIR",     "HeBalloon", "REST"};

struct MuonDISBranches {
  int nDISevts;  // per input muon per volume
  int nDISevtsGenerated =
      -1;                // actual count before filtering; -1 if not crossed
  double pPythia = -1.;  // beam momentum passed to Pythia, in GeV/c
  double wDIS;           // per input muon per volume
  std::vector<double> DISxsec;  // per input muon per DIS
  std::vector<bool> DIStarget;  // per input muon per DIS, p=true, n=false
  std::vector<double> DISvx;
  std::vector<double> DISvy;
  std::vector<double> DISvz;
  std::vector<double> DISvt;
  std::vector<int> nDISdau;               // per DIS event muon
  std::vector<DISparticle> DISparticles;  // all DIS events together.

  void InitTree(TTree* aT, const std::string& aLabel) {
    aT->Branch(("muon_nDISevt_" + aLabel).c_str(), &nDISevts);
    aT->Branch(("muon_nDISGenerated_" + aLabel).c_str(), &nDISevtsGenerated);
    aT->Branch(("muon_pPythia_" + aLabel).c_str(), &pPythia);
    aT->Branch(("muon_wDIS_" + aLabel).c_str(), &wDIS);
    aT->Branch(("mudis_DISxsec_" + aLabel).c_str(), &DISxsec);
    aT->Branch(("mudis_DIStarget_" + aLabel).c_str(), &DIStarget);
    aT->Branch(("mudis_DISvx_" + aLabel).c_str(), &DISvx);
    aT->Branch(("mudis_DISvy_" + aLabel).c_str(), &DISvy);
    aT->Branch(("mudis_DISvz_" + aLabel).c_str(), &DISvz);
    aT->Branch(("mudis_DISvt_" + aLabel).c_str(), &DISvt);
    aT->Branch(("mudis_nDISdaughters_" + aLabel).c_str(), &nDISdau);
    aT->Branch(("mudis_DISproducts_" + aLabel).c_str(), &DISparticles);
  }

  void initEvent(int nDIS) {
    nDISevts = 0;
    nDISevtsGenerated = -1;
    pPythia = -1.;
    wDIS = 1;
    DISxsec.clear();
    DISxsec.reserve(nDIS);
    DIStarget.clear();
    DIStarget.reserve(nDIS);
    DISvx.clear();
    DISvx.reserve(nDIS);
    DISvy.clear();
    DISvy.reserve(nDIS);
    DISvz.clear();
    DISvz.reserve(nDIS);
    DISvt.clear();
    DISvt.reserve(nDIS);
    nDISdau.clear();
    nDISdau.reserve(nDIS);
    DISparticles.clear();
    DISparticles.reserve(10 * nDIS);
  }
};

struct MuonBranches {
  std::vector<ShipMCTrack> mcTrks;
  std::vector<vetoPoint> sbtPt;
  std::vector<UpstreamTaggerPoint> ubtPt;
  std::vector<strawtubesPoint> sstPt;
  std::vector<TimeDetPoint> tdPt;
  double pathLength = 0.;
  std::array<double, nMats> pathLengthByMat = {};
  std::array<MuonDISBranches, nMats> br;
  void InitTree(TTree* aT) {
    aT->Branch("muon_MCTracks", &mcTrks);
    aT->Branch("muon_SBTPoints", &sbtPt);
    aT->Branch("muon_SSTPoints", &sstPt);
    aT->Branch("muon_UBTPoints", &ubtPt);
    aT->Branch("muon_TDPoints", &tdPt);
    aT->Branch("muon_path_length", &pathLength);
    for (unsigned i(0); i < nMats; ++i) {
      aT->Branch(("muon_path_length_" + MatTypeStr[i]).c_str(),
                 &pathLengthByMat[i]);
      br[i].InitTree(aT, MatTypeStr[i]);
    }
  }
  void initEvent(int nMax = 100) {
    mcTrks.clear();
    mcTrks.reserve(nMax);
    sbtPt.clear();
    sbtPt.reserve(nMax);
    ubtPt.clear();
    ubtPt.reserve(nMax);
    sstPt.clear();
    sstPt.reserve(nMax);
    tdPt.clear();
    tdPt.reserve(nMax);
    pathLength = 0.;
    pathLengthByMat.fill(0.);
  }
};

// Bind only on the current file's tree, never on TChain's persistent address
// list. This checks both presence and type when a chain changes files.
template <class T>
bool BindInputBranch(TTree* tree, const std::string& name, T* address,
                     bool required = true) {
  auto* branch = tree->GetBranch(name.c_str());
  if (!branch) {
    if (required) LOG(error) << "Missing required input branch " << name;
    return !required;
  }
  if constexpr (std::is_arithmetic_v<T>) {
    // Reject object branches before ROOT attempts to bind a scalar address.
    if (branch->GetClassName()[0] != '\0') {
      LOG(error) << "Expected scalar input branch " << name;
      return false;
    }
  }
  branch->SetAutoDelete(false);
  return tree->SetBranchAddress(name.c_str(), address) >= 0;
}

struct CBMSimBranches {
  std::vector<ShipMCTrack>* MCTrack = nullptr;
  std::vector<vetoPoint>* sbtPt = nullptr;
  std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
  std::vector<strawtubesPoint>* sstPt = nullptr;
  std::vector<TimeDetPoint>* tdPt = nullptr;

  bool Setup(TChain* tree) {
    fTreeNumber = -1;
    Clear();
    return tree->GetEntries() == 0 || PrepareEntry(tree, 0);
  }

  bool PrepareEntry(TTree* tree, std::int64_t entry) {
    Clear();
    if (tree->LoadTree(entry) < 0) return false;
    if (tree->GetTreeNumber() != fTreeNumber) {
      fTreeNumber = tree->GetTreeNumber();
      auto* current = tree->GetTree();
      fValid = BindInputBranch(current, "MCTrack", &MCTrack);
      fValid &= BindInputBranch(current, "TimeDetPoint", &tdPt);
      fValid &= BindInputBranch(current, "vetoPoint", &sbtPt);
      fValid &= BindInputBranch(current, "UpstreamTaggerPoint", &ubtPt);
      fValid &= BindInputBranch(current, "strawtubesPoint", &sstPt);
    }
    return fValid;
  }

 private:
  void Clear() {
    fTracks.clear();
    fSBT.clear();
    fUBT.clear();
    fSST.clear();
    fTD.clear();
    MCTrack = &fTracks;
    sbtPt = &fSBT;
    ubtPt = &fUBT;
    sstPt = &fSST;
    tdPt = &fTD;
  }
  std::vector<ShipMCTrack> fTracks;
  std::vector<vetoPoint> fSBT;
  std::vector<UpstreamTaggerPoint> fUBT;
  std::vector<strawtubesPoint> fSST;
  std::vector<TimeDetPoint> fTD;
  int fTreeNumber = -1;
  bool fValid = false;
};

// For reading back the DIS tree
struct MuonDISInBranches {
  int nDISevts = 0;  // per input muon per volume
  int nDISevtsGenerated = -1;
  double pPythia = -1.;
  double wDIS = 1;                         // per input muon per volume
  std::vector<double>* DISxsec = nullptr;  // per input muon per DIS
  std::vector<bool>* DIStarget =
      nullptr;  // per input muon per DIS, p=true, n=false
  std::vector<double>* DISvx = nullptr;
  std::vector<double>* DISvy = nullptr;
  std::vector<double>* DISvz = nullptr;
  std::vector<double>* DISvt = nullptr;
  std::vector<int>* nDISdau = nullptr;               // per DIS event muon
  std::vector<DISparticle>* DISparticles = nullptr;  // all DIS events together.

  bool IsValid() const {
    if (nDISevts < 0 || !DISxsec || !DIStarget || !DISvx || !DISvy || !DISvz ||
        !DISvt || !nDISdau || !DISparticles)
      return false;
    const auto size = static_cast<std::size_t>(nDISevts);
    if (DISxsec->size() != size || DIStarget->size() != size ||
        DISvx->size() != size || DISvy->size() != size ||
        DISvz->size() != size || DISvt->size() != size ||
        nDISdau->size() != size)
      return false;
    std::size_t total = 0;
    for (int count : *nDISdau) {
      if (count < 0 ||
          static_cast<std::size_t>(count) > DISparticles->size() - total)
        return false;
      total += count;
    }
    return total == DISparticles->size();
  }

  void Clear() {
    nDISevts = 0;
    nDISevtsGenerated = -1;
    pPythia = -1.;
    wDIS = 1.;
    fStorage.initEvent(0);
    DISxsec = &fStorage.DISxsec;
    DIStarget = &fStorage.DIStarget;
    DISvx = &fStorage.DISvx;
    DISvy = &fStorage.DISvy;
    DISvz = &fStorage.DISvz;
    DISvt = &fStorage.DISvt;
    nDISdau = &fStorage.nDISdau;
    DISparticles = &fStorage.DISparticles;
  }

  bool SetupTree(TTree* tree, const std::string& label) {
    Clear();
    bool ok = BindInputBranch(tree, "muon_nDISevt_" + label, &nDISevts);
    ok &= BindInputBranch(tree, "muon_nDISGenerated_" + label,
                          &nDISevtsGenerated);
    ok &= BindInputBranch(tree, "muon_pPythia_" + label, &pPythia);
    ok &= BindInputBranch(tree, "muon_wDIS_" + label, &wDIS);
    ok &= BindInputBranch(tree, "mudis_DISxsec_" + label, &DISxsec);
    ok &= BindInputBranch(tree, "mudis_DIStarget_" + label, &DIStarget);
    ok &= BindInputBranch(tree, "mudis_DISvx_" + label, &DISvx);
    ok &= BindInputBranch(tree, "mudis_DISvy_" + label, &DISvy);
    ok &= BindInputBranch(tree, "mudis_DISvz_" + label, &DISvz);
    ok &= BindInputBranch(tree, "mudis_DISvt_" + label, &DISvt);
    ok &= BindInputBranch(tree, "mudis_nDISdaughters_" + label, &nDISdau);
    ok &= BindInputBranch(tree, "mudis_DISproducts_" + label, &DISparticles);
    return ok;
  }

  template <class T>
  std::string Print(const std::vector<T>& aVec, const std::string& aName) {
    std::ostringstream lOut;
    lOut << " - " << aName << " size " << aVec.size() << " pointer " << &aVec
         << ": ";
    for (const auto& value : aVec) {
      lOut << value << " ";
    }
    lOut << '\n';
    return lOut.str();
  }

  std::string Print(unsigned aEvt, const std::string& aLabel) {
    std::ostringstream lOut;
    lOut << "------------ print evt " << aEvt << " branch " << aLabel
         << " -------------\n"
         << " - nDISevts = " << nDISevts << '\n'
         << " - wDIS = " << wDIS << '\n';
    if (DISxsec) lOut << Print(*DISxsec, "DISxsec");
    if (DIStarget) lOut << Print(*DIStarget, "DIStarget");
    if (DISvx) lOut << Print(*DISvx, "DISvx");
    if (DISvy) lOut << Print(*DISvy, "DISvy");
    if (DISvz) lOut << Print(*DISvz, "DISvz");
    if (DISvt) lOut << Print(*DISvt, "DISvt");
    if (nDISdau) lOut << Print(*nDISdau, "nDISdau");
    if (DISparticles) lOut << Print(*DISparticles, "DISparticles");

    return lOut.str();
  }

 private:
  MuonDISBranches fStorage;
};

struct MuonInBranches {
  std::vector<ShipMCTrack>* mcTrks = nullptr;
  std::vector<vetoPoint>* sbtPt = nullptr;
  std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
  std::vector<strawtubesPoint>* sstPt = nullptr;
  std::vector<TimeDetPoint>* tdPt = nullptr;
  double pathLength = 0.;
  std::array<double, nMats> pathLengthByMat = {};
  std::array<MuonDISInBranches, nMats> br;

  bool Setup(TTree* tree) {
    fTreeNumber = -1;
    Clear();
    return tree->GetEntries() == 0 || PrepareEntry(tree, 0);
  }

  bool PrepareEntry(TTree* tree, std::int64_t entry) {
    Clear();
    if (tree->LoadTree(entry) < 0) return false;
    if (tree->GetTreeNumber() != fTreeNumber) {
      fTreeNumber = tree->GetTreeNumber();
      auto* current = tree->GetTree();
      fValid = BindInputBranch(current, "muon_MCTracks", &mcTrks);
      fValid &= BindInputBranch(current, "muon_TDPoints", &tdPt);
      fValid &= BindInputBranch(current, "muon_SBTPoints", &sbtPt);
      fValid &= BindInputBranch(current, "muon_UBTPoints", &ubtPt);
      fValid &= BindInputBranch(current, "muon_SSTPoints", &sstPt);
      fValid &= BindInputBranch(current, "muon_path_length", &pathLength);
      for (unsigned i = 0; i < nMats; ++i) {
        const std::string name = "muon_path_length_" + MatTypeStr[i];
        fValid &= BindInputBranch(current, name, &pathLengthByMat[i]);
        fValid &= br[i].SetupTree(current, MatTypeStr[i]);
      }
    }
    return fValid;
  }

 private:
  void Clear() {
    fTracks.clear();
    fSBT.clear();
    fUBT.clear();
    fSST.clear();
    fTD.clear();
    mcTrks = &fTracks;
    sbtPt = &fSBT;
    ubtPt = &fUBT;
    sstPt = &fSST;
    tdPt = &fTD;
    pathLength = 0.;
    pathLengthByMat.fill(0.);
    for (auto& material : br) material.Clear();
  }
  std::vector<ShipMCTrack> fTracks;
  std::vector<vetoPoint> fSBT;
  std::vector<UpstreamTaggerPoint> fUBT;
  std::vector<strawtubesPoint> fSST;
  std::vector<TimeDetPoint> fTD;
  int fTreeNumber = -1;
  bool fValid = false;
};

}  // namespace ShipMuDIS

#endif  // NEWMUONDIS_MUDISDEFS_H_
