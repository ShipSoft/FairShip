// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUDISDEFS_H_
#define NEWMUONDIS_MUDISDEFS_H_

#include <array>
#include <iostream>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>

#include "DISparticle.h"
#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "FairMCEventHeader.h"
#include "ShipMCTrack.h"
#include "TChain.h"  // for TTree
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TVector3.h"
#include "TimeDetPoint.h"
#include "UpstreamTaggerPoint.h"
#include "strawtubesPoint.h"
#include "vetoPoint.h"

namespace ShipMuDIS {
static const unsigned nMats = 10;
// Last shield material in accumulated z (cm), excluding gaps.
inline constexpr double kMuonShieldTailZ = 20.;

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

inline const std::array<TString, nMats> MatTypeStr = {
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
  // Position of the interaction in the prepareEvents output, kept by filtering.
  std::vector<int> DISgenIndex;
  std::vector<double> DISvx;
  std::vector<double> DISvy;
  std::vector<double> DISvz;
  std::vector<double> DISvt;
  std::vector<int> nDISdau;               // per DIS event muon
  std::vector<DISparticle> DISparticles;  // all DIS events together.

  void InitTree(TTree*& aT, const TString& aLabel) {
    aT->Branch("muon_nDISevt_" + aLabel, &nDISevts);
    aT->Branch("muon_nDISGenerated_" + aLabel, &nDISevtsGenerated);
    aT->Branch("muon_pPythia_" + aLabel, &pPythia);
    aT->Branch("muon_wDIS_" + aLabel, &wDIS);
    aT->Branch("mudis_DISxsec_" + aLabel, &DISxsec);
    aT->Branch("mudis_DIStarget_" + aLabel, &DIStarget);
    aT->Branch("mudis_DISgenIndex_" + aLabel, &DISgenIndex);
    aT->Branch("mudis_DISvx_" + aLabel, &DISvx);
    aT->Branch("mudis_DISvy_" + aLabel, &DISvy);
    aT->Branch("mudis_DISvz_" + aLabel, &DISvz);
    aT->Branch("mudis_DISvt_" + aLabel, &DISvt);
    aT->Branch("mudis_nDISdaughters_" + aLabel, &nDISdau);
    aT->Branch("mudis_DISproducts_" + aLabel, &DISparticles);
  };

  void initEvent(const int& nDIS) {
    nDISevts = 0;
    nDISevtsGenerated = -1;
    pPythia = -1.;
    wDIS = 1;
    DISxsec.clear();
    DISxsec.reserve(nDIS);
    DIStarget.clear();
    DIStarget.reserve(nDIS);
    DISgenIndex.clear();
    DISgenIndex.reserve(nDIS);
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
  };
};

// Where an input muon comes from; -1 where unknown. See README.md.
struct MuonSource {
  Int_t file = -1;        // index into the FileSummary inputFiles
  Long64_t entry = -1;    // entry of the muon's event in that file's cbmsim
  Int_t trackID = -1;     // index of the muon in that event's MCTrack
  Long64_t runID = -1;    // MCEventHeader RunID of that event
  Long64_t eventID = -1;  // MCEventHeader EventID of that event
  // muBack_srcRunID and muBack_srcEventID of that event: the input event of
  // the MuonBackGenerator simulation that produced it, i.e. the PoT event
  // when that input was the PoT simulation.
  Long64_t potRunID = -1;
  Long64_t potEventID = -1;

  void Reset() { *this = MuonSource(); }
};

inline const std::array<TString, 7> MuonSourceBranchNames = {
    "muon_srcFile",    "muon_srcEntry", "muon_srcTrackID", "muon_srcRunID",
    "muon_srcEventID", "muon_potRunID", "muon_potEventID"};

struct MuonBranches {
  std::vector<ShipMCTrack> mcTrks;
  std::vector<vetoPoint> sbtPt;
  std::vector<UpstreamTaggerPoint> ubtPt;
  std::vector<strawtubesPoint> sstPt;
  std::vector<TimeDetPoint> tdPt;
  double pathLength = 0.;
  std::array<double, nMats> pathLengthByMat = {};
  MuonSource source;
  MuonDISBranches br[nMats];
  void InitTree(TTree*& aT) {
    aT->Branch("muon_MCTracks", &mcTrks);
    aT->Branch("muon_SBTPoints", &sbtPt);
    aT->Branch("muon_SSTPoints", &sstPt);
    aT->Branch("muon_UBTPoints", &ubtPt);
    aT->Branch("muon_TDPoints", &tdPt);
    aT->Branch("muon_path_length", &pathLength);
    aT->Branch(MuonSourceBranchNames[0], &source.file);
    aT->Branch(MuonSourceBranchNames[1], &source.entry);
    aT->Branch(MuonSourceBranchNames[2], &source.trackID);
    aT->Branch(MuonSourceBranchNames[3], &source.runID);
    aT->Branch(MuonSourceBranchNames[4], &source.eventID);
    aT->Branch(MuonSourceBranchNames[5], &source.potRunID);
    aT->Branch(MuonSourceBranchNames[6], &source.potEventID);
    for (unsigned i(0); i < nMats; ++i) {
      aT->Branch("muon_path_length_" + MatTypeStr[i], &pathLengthByMat[i]);
      br[i].InitTree(aT, MatTypeStr[i]);
    }
  };
  void initEvent(const int& nMax = 100) {
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
    source.Reset();
  };
};

// Bind only on the current file's tree, never on TChain's persistent address
// list. This checks both presence and type when a chain changes files.
template <class T>
bool BindInputBranch(TTree* tree, const TString& name, T* address,
                     bool required = true) {
  auto* branch = tree->GetBranch(name);
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
  return tree->SetBranchAddress(name, address) >= 0;
}

struct CBMSimBranches {
  std::vector<ShipMCTrack>* MCTrack = nullptr;
  std::vector<vetoPoint>* sbtPt = nullptr;
  std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
  std::vector<strawtubesPoint>* sstPt = nullptr;
  std::vector<TimeDetPoint>* tdPt = nullptr;
  // Event header of the current input file; valid only if HasHeader().
  FairMCEventHeader* header = nullptr;
  // Written by MuonBackGenerator; -1 if the input has no such branches.
  Long64_t muBackRunID = -1;
  Long64_t muBackEventID = -1;

  bool HasHeader() const { return fHasHeader; }

  bool Setup(TChain* tree) {
    fTreeNumber = -1;
    Clear();
    return tree->GetEntries() == 0 || PrepareEntry(tree, 0);
  }

  bool PrepareEntry(TTree* tree, Long64_t entry) {
    Clear();
    if (tree->LoadTree(entry) < 0) return false;
    if (tree->GetTreeNumber() != fTreeNumber) {
      fTreeNumber = tree->GetTreeNumber();
      auto* current = tree->GetTree();
      fHasHeader = current->GetBranch("MCEventHeader.") != nullptr &&
                   BindInputBranch(current, "MCEventHeader.", &header, false);
      fValid = BindInputBranch(current, "muBack_srcRunID", &muBackRunID, false);
      fValid &=
          BindInputBranch(current, "muBack_srcEventID", &muBackEventID, false);
      fValid &= BindInputBranch(current, "MCTrack", &MCTrack);
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
    header = &fHeader;
    muBackRunID = -1;
    muBackEventID = -1;
  }
  std::vector<ShipMCTrack> fTracks;
  std::vector<vetoPoint> fSBT;
  std::vector<UpstreamTaggerPoint> fUBT;
  std::vector<strawtubesPoint> fSST;
  std::vector<TimeDetPoint> fTD;
  FairMCEventHeader fHeader;
  int fTreeNumber = -1;
  bool fValid = false;
  bool fHasHeader = false;
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
  // Missing from files written before it was introduced; use GenIndex().
  std::vector<int>* DISgenIndex = nullptr;
  std::vector<double>* DISvx = nullptr;
  std::vector<double>* DISvy = nullptr;
  std::vector<double>* DISvz = nullptr;
  std::vector<double>* DISvt = nullptr;
  std::vector<int>* nDISdau = nullptr;               // per DIS event muon
  std::vector<DISparticle>* DISparticles = nullptr;  // all DIS events together.

  // Position of DIS interaction i in the prepareEvents output, or -1 if the
  // input does not record it.
  int GenIndex(int i) const {
    return fHasGenIndex ? DISgenIndex->at(static_cast<std::size_t>(i)) : -1;
  }

  bool IsValid() const {
    if (nDISevts < 0 || !DISxsec || !DIStarget || !DISgenIndex || !DISvx ||
        !DISvy || !DISvz || !DISvt || !nDISdau || !DISparticles)
      return false;
    const auto size = static_cast<std::size_t>(nDISevts);
    if (fHasGenIndex && DISgenIndex->size() != size) return false;
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
    DISgenIndex = &fStorage.DISgenIndex;
    DISvx = &fStorage.DISvx;
    DISvy = &fStorage.DISvy;
    DISvz = &fStorage.DISvz;
    DISvt = &fStorage.DISvt;
    nDISdau = &fStorage.nDISdau;
    DISparticles = &fStorage.DISparticles;
  }

  bool SetupTree(TTree* tree, const TString& label) {
    Clear();
    bool ok = BindInputBranch(tree, "muon_nDISevt_" + label, &nDISevts);
    ok &= BindInputBranch(tree, "muon_nDISGenerated_" + label,
                          &nDISevtsGenerated);
    ok &= BindInputBranch(tree, "muon_pPythia_" + label, &pPythia);
    ok &= BindInputBranch(tree, "muon_wDIS_" + label, &wDIS);
    ok &= BindInputBranch(tree, "mudis_DISxsec_" + label, &DISxsec);
    ok &= BindInputBranch(tree, "mudis_DIStarget_" + label, &DIStarget);
    fHasGenIndex = tree->GetBranch("mudis_DISgenIndex_" + label) != nullptr;
    ok &= BindInputBranch(tree, "mudis_DISgenIndex_" + label, &DISgenIndex,
                          false);
    ok &= BindInputBranch(tree, "mudis_DISvx_" + label, &DISvx);
    ok &= BindInputBranch(tree, "mudis_DISvy_" + label, &DISvy);
    ok &= BindInputBranch(tree, "mudis_DISvz_" + label, &DISvz);
    ok &= BindInputBranch(tree, "mudis_DISvt_" + label, &DISvt);
    ok &= BindInputBranch(tree, "mudis_nDISdaughters_" + label, &nDISdau);
    ok &= BindInputBranch(tree, "mudis_DISproducts_" + label, &DISparticles);
    return ok;
  }

  template <class T>
  std::string Print(const std::vector<T>& aVec, const TString& aName) {
    std::ostringstream lOut;
    lOut << " - " << aName << " size " << aVec.size() << " pointer " << &aVec
         << ": ";
    for (const auto& value : aVec) {
      lOut << value << " ";
    }
    lOut << std::endl;
    return lOut.str();
  };

  std::ostringstream Print(const unsigned& aEvt, const TString& aLabel) {
    std::ostringstream lOut;
    lOut << "------------ print evt " << aEvt << " branch " << aLabel
         << " -------------" << std::endl
         << " - nDISevts = " << nDISevts << std::endl
         << " - wDIS = " << wDIS << std::endl;
    if (DISxsec) lOut << Print(*DISxsec, "DISxsec");
    if (DIStarget) lOut << Print(*DIStarget, "DIStarget");
    if (fHasGenIndex) lOut << Print(*DISgenIndex, "DISgenIndex");
    if (DISvx) lOut << Print(*DISvx, "DISvx");
    if (DISvy) lOut << Print(*DISvy, "DISvy");
    if (DISvz) lOut << Print(*DISvz, "DISvz");
    if (DISvt) lOut << Print(*DISvt, "DISvt");
    if (nDISdau) lOut << Print(*nDISdau, "nDISdau");
    if (DISparticles) lOut << Print(*DISparticles, "DISparticles");

    return lOut;
  };

 private:
  MuonDISBranches fStorage;
  bool fHasGenIndex = false;
};

struct MuonInBranches {
  std::vector<ShipMCTrack>* mcTrks = nullptr;
  std::vector<vetoPoint>* sbtPt = nullptr;
  std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
  std::vector<strawtubesPoint>* sstPt = nullptr;
  std::vector<TimeDetPoint>* tdPt = nullptr;
  double pathLength = 0.;
  std::array<double, nMats> pathLengthByMat = {};
  // Optional: files written before these branches existed leave them at -1.
  MuonSource source;
  MuonDISInBranches br[nMats];

  bool Setup(TTree* tree) {
    fTreeNumber = -1;
    Clear();
    return tree->GetEntries() == 0 || PrepareEntry(tree, 0);
  }

  bool PrepareEntry(TTree* tree, Long64_t entry) {
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
      fValid &= BindInputBranch(current, MuonSourceBranchNames[0], &source.file,
                                false);
      fValid &= BindInputBranch(current, MuonSourceBranchNames[1],
                                &source.entry, false);
      fValid &= BindInputBranch(current, MuonSourceBranchNames[2],
                                &source.trackID, false);
      fValid &= BindInputBranch(current, MuonSourceBranchNames[3],
                                &source.runID, false);
      fValid &= BindInputBranch(current, MuonSourceBranchNames[4],
                                &source.eventID, false);
      fValid &= BindInputBranch(current, MuonSourceBranchNames[5],
                                &source.potRunID, false);
      fValid &= BindInputBranch(current, MuonSourceBranchNames[6],
                                &source.potEventID, false);
      for (unsigned i = 0; i < nMats; ++i) {
        const TString name = "muon_path_length_" + MatTypeStr[i];
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
    source.Reset();
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
