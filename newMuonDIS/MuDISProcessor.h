// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUDISPROCESSOR_H_
#define NEWMUONDIS_MUDISPROCESSOR_H_

#include <memory>
#include <string>
#include <vector>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Math/Vector3D.h"
#include "MuDISDefs.h"
#include "MuGeoProcessor.h"
#include "MuonPath.h"
#include "TChain.h"  // for TTree
#include "TPythia6.h"
#include "TPythia6Calls.h"

class MuDISProcessor {
 public:
  /** default constructor **/
  MuDISProcessor();

  bool init(int aEvts, int aStart, double aMinPythiaP, int aDIS, int aSeed,
            double aZmax, double aZmin = 2500);
  void initPythia6();

  static ROOT::Math::XYZVector rotate(const ROOT::Math::XYZVector& pvec,
                                      double theta, double phi);

  bool InitFile(const char*, int);
  bool InitFile(const char*);
  bool InitFiles(const std::vector<std::string>&, int);
  bool InitFiles(const std::vector<std::string>&);
  void process_file(const std::string& input, const std::string& output);
  void process_file(const std::vector<std::string>& input,
                    const std::string& output);
  void initEvent();
  void fillMCTracks(const int aIdx);
  void fillSBTHits(const int aIdx);
  void fillUBTHits(const int aIdx);
  void fillSSTHits(const int aIdx);
  void fillTDHits(const int aIdx);
  void CheckAllVolumes() { fGeoProcessor.CheckAllVolumes(); }
  void SetMuonShieldField(ShipBFieldMap* field, TGeoManager* geometry) {
    fGeoProcessor.SetMuonShieldField(field, geometry);
  }
  void SetPocaJumpThreshold(double threshold) {
    fGeoProcessor.SetPocaJumpThreshold(threshold);
  }

  void generateDISevents(const std::string& tType, double amuonW,
                         const std::string& aLabel, const MuonPath& aPath,
                         ShipMuDIS::MuonDISBranches& aDISBr);

  void ProcessMuons();

 private:
  std::unique_ptr<TChain> ftree;
  ShipMuDIS::CBMSimBranches finEv;

  TTree* fouttree = nullptr;
  ShipMuDIS::MuonBranches foutEv;

  int fnEvts = -1;
  int fstartEvt = 0;

  TPythia6* fPythia;

  double fMinPythiaP = 2;
  int fnDIS = 10;
  int fP6seed = 0;

  MuGeoProcessor fGeoProcessor;

  // void FillMuonTracks(int muon_id);
  // void FillVetoPoints(int muon_id);
  // void FillUBTPoints(int muon_id);
  // void FillSSTPoints(int muon_id);
};

#endif  // NEWMUONDIS_MUDISPROCESSOR_H_
