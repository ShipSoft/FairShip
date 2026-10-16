// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUDISPROCESSOR_H_
#define NEWMUONDIS_MUDISPROCESSOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "MuDISDefs.h"
#include "MuGeoProcessor.h"
#include "MuonPath.h"
#include "TChain.h"  // for TTree
#include "TPythia6.h"
#include "TPythia6Calls.h"
#include "TROOT.h"
#include "TVector3.h"
#include "vector"

class MuDISProcessor {
 public:
  /** default constructor **/
  MuDISProcessor();

  /** destructor **/
  ~MuDISProcessor() { delete ftree; }

  bool init(const int& aEvts, const int& aStart, const double& aMinPythiaP,
            const int& aDIS, const int& aSeed, const double& aZmax,
            const double& aZmin = 2500);
  void initPythia6();

  void rotate(const TVector3& pvec, const double& theta, const double& phi,
              TVector3& newp);

  Bool_t InitFile(const char*, int);
  Bool_t InitFile(const char*);
  Bool_t InitFiles(const std::vector<std::string>&, int);
  Bool_t InitFiles(const std::vector<std::string>&);
  void process_file(const std::string& input, const std::string& output);
  void process_file(const std::vector<std::string>& input,
                    const std::string& output);
  void initEvent();
  void fillMCTracks(const Int_t aIdx);
  void fillSBTHits(const Int_t aIdx);
  void fillUBTHits(const Int_t aIdx);
  void fillSSTHits(const Int_t aIdx);
  void fillTDHits(const Int_t aIdx);
  void CheckAllVolumes() { fGeoProcessor.CheckAllVolumes(); }
  void SetMuonShieldField(ShipBFieldMap* field, TGeoManager* geometry) {
    fGeoProcessor.SetMuonShieldField(field, geometry);
  }
  void SetPocaJumpThreshold(double threshold) {
    fGeoProcessor.SetPocaJumpThreshold(threshold);
  }
  // Which tracks of an input event are processed as muons (see README.md):
  // "first" MCTrack[0], which must be a muon (particle-gun input); "hits"
  // every muon track with a UBT, SBT, SST or TD point; "all" every muon track;
  // "auto" (default) "first" if MCTrack[0] is a muon, else "hits".
  // Returns false for an unknown name.
  bool SetMuonSelection(const std::string& selection);
  // Indices in the current event's MCTrack of the tracks to process.
  std::vector<Int_t> SelectMuons() const;

  void generateDISevents(const std::string& tType, const double& amuonW,
                         const std::string& aLabel, const MuonPath& aPath,
                         ShipMuDIS::MuonDISBranches& aDISBr);

  void ProcessMuons();

 private:
  TChain* ftree;
  ShipMuDIS::CBMSimBranches finEv;

  TTree* fouttree;
  ShipMuDIS::MuonBranches foutEv;

  FairLogger* fLogger;  //!   don't make it persistent, magic ROOT command
  int fnEvts;
  int fstartEvt;

  TPythia6* fPythia;

  double fMinPythiaP;
  int fnDIS;
  int fP6seed;
  enum class MuonSelection { kAuto, kFirst, kWithHits, kAll };
  MuonSelection fMuonSelection = MuonSelection::kAuto;

  MuGeoProcessor fGeoProcessor;

  // void FillMuonTracks(int muon_id);
  // void FillVetoPoints(int muon_id);
  // void FillUBTPoints(int muon_id);
  // void FillSSTPoints(int muon_id);
};

#endif  // NEWMUONDIS_MUDISPROCESSOR_H_
