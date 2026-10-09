// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MAGNETICTRACKPROPAGATOR_H_
#define NEWMUONDIS_MAGNETICTRACKPROPAGATOR_H_

#include <array>
#include <cstddef>
#include <limits>
#include <utility>
#include <vector>

#include "Math/Point3D.h"
#include "Math/Vector3D.h"

class ShipBFieldMap;
class TGeoManager;

// Magnetic transport only: cm, GeV/c, charge in units of e. The momentum
// vector supplies both magnitude and direction. Field/geometry are borrowed
// and must remain alive and unchanged while this object is used.
class MagneticTrackPropagator {
 public:
  explicit MagneticTrackPropagator(ShipBFieldMap* field = nullptr,
                                   TGeoManager* geometry = nullptr,
                                   ShipBFieldMap* muonShieldField = nullptr);
  void SetAccuracy(double positionTolerance = 1.e-3,
                   double relativeMomentumTolerance = 1.e-6,
                   double maxStep = 5.);
  double GetPlaneZ(const char* volumeName = "Tr1") const;
  std::pair<double, double> GetVolumeZRange(const char* volumeName) const;
  // Global x/y limits of the downstream (+local-z) face of a box volume.
  std::array<double, 4> GetVolumeExitFaceXY(const char* volumeName) const;
  std::pair<double, double> GetMuonShieldZRange() const {
    return fMuonShieldZRange;
  }
  bool HasMuonShieldField() const { return fMuonShieldField != nullptr; }
  // Restrict the initial shield scan; a later upstream request widens it
  // safely.
  void SetMuonShieldMinZ(double minimumZ);
  double GetMuonShieldMinZ() const { return fMuonShieldMinZ; }
  // Test a forward trajectory against an axis-aligned detector volume.
  bool IntersectsBox(double charge, const ROOT::Math::XYZPoint& position,
                     const ROOT::Math::XYZVector& momentum,
                     const ROOT::Math::XYZPoint& minimum,
                     const ROOT::Math::XYZPoint& maximum) const;

  // Both directions in z are supported, provided pz never changes sign.
  // False means invalid input, a turning track, or failure to converge.
  bool Extrapolate(double charge, const ROOT::Math::XYZPoint& position,
                   const ROOT::Math::XYZVector& momentum, double z,
                   ROOT::Math::XYZPoint& result,
                   ROOT::Math::XYZVector& resultMomentum) const;
  bool BuildTrajectory(double charge, const ROOT::Math::XYZPoint& position,
                       const ROOT::Math::XYZVector& momentum, double endZ);
  // Cubic interpolation of cached positions; never evaluates the field.
  bool PositionAt(double z, ROOT::Math::XYZPoint& position) const;
  std::size_t GetTrajectorySize() const { return fTrajectory.size(); }
  bool GetTrajectoryState(std::size_t index, ROOT::Math::XYZPoint& position,
                          ROOT::Math::XYZVector& momentum) const;
  // Downstream end of all nonzero interpolation cells, including fringes.
  double GetFieldEndZ(double minimumZ) const;
  // Evaluate the map at the point, including interpolation and fringes.
  bool HasFieldAt(const ROOT::Math::XYZPoint& position) const;

 private:
  struct State {
    ROOT::Math::XYZPoint position;
    ROOT::Math::XYZVector momentum;
  };
  // d(State)/dz: track slope and momentum change per unit z.
  struct StateDerivative {
    ROOT::Math::XYZVector slope;
    ROOT::Math::XYZVector momentum;
  };
  struct Box {
    std::array<double, 3> minimum, maximum;
  };
  struct FieldMap {
    ShipBFieldMap* field;  // Borrowed; the caller owns the map.
    std::vector<Box> regions;
    double gridStep;
  };
  static bool InsideBox(const ROOT::Math::XYZPoint& position, const Box& box);
  static bool RayBoxInterval(const ROOT::Math::XYZPoint& position,
                             const ROOT::Math::XYZVector& direction,
                             const Box& box, double& entry, double& exit);
  static bool SegmentIntersectsBox(const State& start, const State& end,
                                   const Box& box);
  void AddFieldMap(ShipBFieldMap* field, double minimumZ) const;
  void EnsureMuonShield(double minimumZ) const;
  bool Derivative(const State& state, double charge, double pzSign,
                  StateDerivative& derivative) const;
  bool RKStep(const State& state, double charge, double pzSign, double dz,
              State& result) const;
  bool Propagate(double charge, const ROOT::Math::XYZPoint& position,
                 const ROOT::Math::XYZVector& momentum, double z, State& result,
                 std::vector<State>* trajectory,
                 const Box* box = nullptr) const;
  TGeoManager* fGeometry;  //! Borrowed geometry
  mutable std::vector<FieldMap>
      fFields;  //! Maps and conservative nonzero 3D regions
  ShipBFieldMap* fMuonShieldField =
      nullptr;  //! Borrowed; scanned on first transport
  mutable bool fMuonShieldReady = false;
  mutable double fMuonShieldMinZ = -std::numeric_limits<double>::infinity();
  std::pair<double, double> fMuonShieldZRange = {0., 0.};
  double fPositionTolerance = 1.e-3;
  double fMomentumTolerance = 1.e-6;
  double fMaxStep = 5.;
  std::vector<State> fTrajectory;  //! Runtime trajectory cache
};

#endif  // NEWMUONDIS_MAGNETICTRACKPROPAGATOR_H_
