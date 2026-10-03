// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef SHIPMuDIS_MUGEOPROCESSOR_H_
#define SHIPMuDIS_MUGEOPROCESSOR_H_

#include <array>
#include <map>
#include <set>
#include <string>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "MuDISDefs.h"
#include "MuonPath.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoNode.h"
#include "TGeoShape.h"
#include "TGeoVolume.h"
#include "TMath.h"
#include "TVector3.h"

class MuGeoProcessor {
 public:
  /** default constructor **/
  MuGeoProcessor();

  /** destructor **/
  ~MuGeoProcessor();

  bool initialise(ShipMuDIS::MuonBranches& aEvt);
  void SetPocaJumpThreshold(double threshold);
  double GetPocaJumpThreshold() const { return fPocaJumpThreshold; }
  void ResetDiagnostics();
  void PrintDiagnostics() const;
  unsigned long long GetLargeJumpCount() const { return fLargeJumps; }
  unsigned long long GetMuonsWithLargeJumps() const { return fMuonsWithLargeJumps; }
  unsigned long long GetBackwardMuonCount() const { return fBackwardMuons; }
  double GetMaxTransverseJump() const { return fMaxTransverseJump; }

  inline void SetZmax(const double& zmax) {
    LOG(info) << " Maximum z position for MuonPath building: " << zmax
              << " cm.";
    fZmax = zmax;
  };
  inline void SetZmin(const double& zmin) {
    LOG(info) << " Minimum z position for MuonPath building: " << zmin
              << " cm.";
    fZmin = zmin;
  };

  inline double FindZmax(const std::string& aLabel) {
    auto it = fZmaxMap.find(aLabel);
    if (it != fZmaxMap.end())
      return it->second;
    else {
      LOG(error) << " * MuGeoProcessor::FindZmax() Volume label " << aLabel
                 << " not found, using default Zmax: " << fZmax << "."
                 << std::endl;
      return fZmax;
    }
  };

  TVector3 GetVertex(const TVector3& r1, const TVector3& p1, const TVector3& r2,
                     const TVector3& p2);
  void CheckAllVolumes();
  void FillZmaxVolumes();
  std::map<std::string, MuonPath>& FillMuonPath();
  void PrintVolumes();

 private:
  double fZmax;
  double fZmin;
  struct Measurement {
    TVector3 position;
    TVector3 momentum;
    double time;
  };
  struct Segment {
    Measurement measurement;
    double startZ;
    double endZ;
  };
  // Start, UBT, SBT, Tr1--Tr4 and TD; no per-muon allocations.
  std::array<Segment, 8> fSegments;  //! Runtime path segments
  unsigned fNSegments = 0;

  double fPocaJumpThreshold = 1.;  // transverse distance in cm
  unsigned long long fMuons = 0;
  unsigned long long fBackwardMuons = 0;
  unsigned long long fInvalidMuons = 0;
  unsigned long long fTransitions = 0;
  unsigned long long fLargeJumps = 0;
  unsigned long long fMuonsWithLargeJumps = 0;
  double fMaxTransverseJump = 0.;

  std::map<std::string, MuonPath> fPathMap;
  std::map<std::string, std::set<std::string>> fVolMap;
  std::map<std::string, double> fZmaxMap;

};  // class

#endif
