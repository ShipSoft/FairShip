// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUGEOPROCESSOR_H_
#define NEWMUONDIS_MUGEOPROCESSOR_H_

#include <array>
#include <map>
#include <memory>
#include <set>
#include <string>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "MagneticTrackPropagator.h"
#include "Math/Point3D.h"
#include "Math/Vector3D.h"
#include "MuDISDefs.h"
#include "MuonPath.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMatrix.h"
#include "TGeoNode.h"
#include "TGeoShape.h"
#include "TGeoVolume.h"

class MuGeoProcessor {
 public:
  /** default constructor **/
  MuGeoProcessor();

  /** destructor **/
  ~MuGeoProcessor();

  bool initialise(ShipMuDIS::MuonBranches& aEvt);
  // The caller retains ownership of the field and geometry.
  void SetMuonShieldField(ShipBFieldMap* field, TGeoManager* geometry);
  void SetPocaJumpThreshold(double threshold);
  double GetPocaJumpThreshold() const { return fPocaJumpThreshold; }
  void ResetDiagnostics();
  void PrintDiagnostics() const;
  int64_t GetLargeJumpCount() const { return fLargeJumps; }
  int64_t GetMuonsWithLargeJumps() const { return fMuonsWithLargeJumps; }
  int64_t GetBackwardMuonCount() const { return fBackwardMuons; }
  int64_t GetUBTBackwardMissCount() const { return fUBTBackwardMisses; }
  int64_t GetUBTBackwardPathCount() const { return fUBTBackwardPaths; }
  int64_t GetStartInFieldCount() const { return fStartMagneticPaths; }
  int64_t GetStartFieldFreeCount() const { return fStartStraightPaths; }
  int64_t GetStartsBeforeZminCount() const { return fStartsBeforeZmin; }
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

  ROOT::Math::XYZPoint GetVertex(const ROOT::Math::XYZPoint& r1,
                                 const ROOT::Math::XYZVector& p1,
                                 const ROOT::Math::XYZPoint& r2,
                                 const ROOT::Math::XYZVector& p2);
  void CheckAllVolumes();
  std::map<std::string, MuonPath>& FillMuonPath();
  void PrintVolumes();

 private:
  double fZmax;
  double fZmin;
  struct Measurement {
    ROOT::Math::XYZPoint position;
    ROOT::Math::XYZVector momentum;
    double time;
  };
  struct Segment {
    Measurement measurement;
    double startZ;
    double endZ;
    bool measurementTransition = true;
  };
  void CacheGeometry();
  bool AddMagneticSegments(const Measurement& start, double charge,
                           double endZ);
  double GetTrajectoryPocaZ(const Measurement& hit) const;
  bool AddMagneticChord(const ROOT::Math::XYZPoint& a,
                        const ROOT::Math::XYZPoint& b, double momentum,
                        double& time, unsigned depth = 0);
  bool Trace(const Measurement& measurement, double startZ, double endZ,
             bool backward = false);
  void AddPath(const MuonPath& path);
  std::vector<Segment> fSegments;              //! Runtime path segments
  std::set<const TGeoVolume*> fShieldVolumes;  //! Shield material volumes
  TGeoManager* fGeometry = nullptr;            //! Borrowed geometry
  TGeoNode* fTopNode = nullptr;                //! Geometry cache identity
  std::unique_ptr<MagneticTrackPropagator> fPropagator;  //! Shield transport
  double fShieldMinZ = 0.;
  bool fTraceBackward = false;
  Measurement fStart, fUBT;

  double fPocaJumpThreshold = 1.;  // transverse distance in cm
  int64_t fMuons = 0;
  int64_t fBackwardMuons = 0;
  int64_t fInvalidMuons = 0;
  // Routes prepared by initialise(), before material navigation.
  int64_t fUBTBackwardPaths = 0;
  int64_t fUBTBackwardMisses = 0;
  int64_t fStartMagneticPaths = 0;
  int64_t fStartStraightPaths = 0;
  int64_t fStartsBeyondZmax = 0;
  int64_t fStartsBeforeZmin = 0;  // diagnostic only; counted per path build
  int64_t fTransitions = 0;
  int64_t fLargeJumps = 0;
  int64_t fMuonsWithLargeJumps = 0;
  double fMaxTransverseJump = 0.;

  std::map<std::string, MuonPath> fPathMap;
  std::map<std::string, std::set<std::string>> fVolMap;

};  // class

#endif  // NEWMUONDIS_MUGEOPROCESSOR_H_
