// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "MagneticTrackPropagator.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>

#include "ShipBFieldMap.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoMatrix.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"

using ROOT::Math::XYZPoint;
using ROOT::Math::XYZVector;

namespace {
template <class V>
bool Finite(const V& v) {
  return std::isfinite(v.X()) && std::isfinite(v.Y()) && std::isfinite(v.Z());
}

template <class V>
std::array<double, 3> Coordinates(const V& v) {
  return {v.X(), v.Y(), v.Z()};
}

bool FindVolume(TGeoNode* node, const TGeoHMatrix& parent,
                const std::string& name, double& z) {
  TGeoHMatrix transform(parent);
  transform.Multiply(node->GetMatrix());
  if (name == node->GetVolume()->GetName()) {
    const double origin[3] = {0., 0., 0.};
    double global[3];
    transform.LocalToMaster(origin, global);
    z = global[2];
    return true;
  }
  for (int i = 0; i < node->GetNdaughters(); ++i)
    if (FindVolume(node->GetDaughter(i), transform, name, z)) return true;
  return false;
}

bool FindVolumeRange(TGeoNode* node, const TGeoHMatrix& parent,
                     const std::string& name,
                     std::pair<double, double>& range) {
  TGeoHMatrix transform(parent);
  transform.Multiply(node->GetMatrix());
  if (name == node->GetVolume()->GetName()) {
    auto* box = dynamic_cast<TGeoBBox*>(node->GetVolume()->GetShape());
    if (!box) throw std::runtime_error("Volume has no bounding box: " + name);
    box->ComputeBBox();
    const auto* origin = box->GetOrigin();
    range = {std::numeric_limits<double>::infinity(),
             -std::numeric_limits<double>::infinity()};
    for (double x : {-box->GetDX(), box->GetDX()})
      for (double y : {-box->GetDY(), box->GetDY()})
        for (double z : {-box->GetDZ(), box->GetDZ()}) {
          const double local[3] = {origin[0] + x, origin[1] + y, origin[2] + z};
          double global[3];
          transform.LocalToMaster(local, global);
          range.first = std::min(range.first, global[2]);
          range.second = std::max(range.second, global[2]);
        }
    return std::isfinite(range.first) && std::isfinite(range.second) &&
           range.first < range.second;
  }
  for (int i = 0; i < node->GetNdaughters(); ++i)
    if (FindVolumeRange(node->GetDaughter(i), transform, name, range))
      return true;
  return false;
}

bool FindVolumeExitFaceXY(TGeoNode* node, const TGeoHMatrix& parent,
                          const std::string& name,
                          std::array<double, 4>& bounds) {
  TGeoHMatrix transform(parent);
  transform.Multiply(node->GetMatrix());
  if (name == node->GetVolume()->GetName()) {
    auto* box = dynamic_cast<TGeoBBox*>(node->GetVolume()->GetShape());
    if (!box) throw std::runtime_error("Volume has no bounding box: " + name);
    box->ComputeBBox();
    const auto* origin = box->GetOrigin();
    bounds = {std::numeric_limits<double>::infinity(),
              -std::numeric_limits<double>::infinity(),
              std::numeric_limits<double>::infinity(),
              -std::numeric_limits<double>::infinity()};
    for (double x : {-box->GetDX(), box->GetDX()})
      for (double y : {-box->GetDY(), box->GetDY()}) {
        const double local[3] = {origin[0] + x, origin[1] + y,
                                 origin[2] + box->GetDZ()};
        double global[3];
        transform.LocalToMaster(local, global);
        bounds[0] = std::min(bounds[0], global[0]);
        bounds[1] = std::max(bounds[1], global[0]);
        bounds[2] = std::min(bounds[2], global[1]);
        bounds[3] = std::max(bounds[3], global[1]);
      }
    return std::isfinite(bounds[0]) && std::isfinite(bounds[1]) &&
           std::isfinite(bounds[2]) && std::isfinite(bounds[3]) &&
           bounds[0] < bounds[1] && bounds[2] < bounds[3];
  }
  for (int i = 0; i < node->GetNdaughters(); ++i)
    if (FindVolumeExitFaceXY(node->GetDaughter(i), transform, name, bounds))
      return true;
  return false;
}
}  // namespace

MagneticTrackPropagator::MagneticTrackPropagator(ShipBFieldMap* field,
                                                 TGeoManager* geometry,
                                                 ShipBFieldMap* muonShieldField)
    : fGeometry(geometry) {
  AddFieldMap(field, -std::numeric_limits<double>::infinity());
  if (muonShieldField) {
    if (!geometry || !geometry->GetTopNode() ||
        !FindVolumeRange(geometry->GetTopNode(), TGeoHMatrix(),
                         "MuonShieldArea", fMuonShieldZRange))
      throw std::runtime_error("MuonShieldArea z range not found in geometry");
    if (muonShieldField == field)
      throw std::invalid_argument("SST and muon shield maps must be distinct");
    fMuonShieldField = muonShieldField;
    // Check alignment without scanning the field values. The shield cache is
    // built after the input vertex range is known.
    TGeoTranslation translation(muonShieldField->GetXOffset(),
                                muonShieldField->GetYOffset(),
                                muonShieldField->GetZOffset());
    TGeoRotation rotation("shieldBounds", muonShieldField->GetPhi(),
                          muonShieldField->GetTheta(),
                          muonShieldField->GetPsi());
    TGeoCombiTrans transform(translation, rotation);
    double low = std::numeric_limits<double>::infinity(), high = -low;
    for (double x : {muonShieldField->HasSymmetry()
                         ? -static_cast<double>(muonShieldField->GetXMax())
                         : static_cast<double>(muonShieldField->GetXMin()),
                     static_cast<double>(muonShieldField->GetXMax())})
      for (double y : {muonShieldField->HasSymmetry()
                           ? -static_cast<double>(muonShieldField->GetYMax())
                           : static_cast<double>(muonShieldField->GetYMin()),
                       static_cast<double>(muonShieldField->GetYMax())})
        for (double z : {static_cast<double>(muonShieldField->GetZMin()),
                         static_cast<double>(muonShieldField->GetZMax())}) {
          const double local[3] = {x, y, z};
          double global[3];
          transform.LocalToMaster(local, global);
          low = std::min(low, global[2]);
          high = std::max(high, global[2]);
        }
    if (low >= fMuonShieldZRange.second || high <= fMuonShieldZRange.first)
      throw std::invalid_argument(
          "Muon shield field does not overlap MuonShieldArea; check its z "
          "offset");
  }
}

void MagneticTrackPropagator::SetAccuracy(double positionTolerance,
                                          double relativeMomentumTolerance,
                                          double maxStep) {
  if (!std::isfinite(positionTolerance) || positionTolerance <= 0. ||
      !std::isfinite(relativeMomentumTolerance) ||
      relativeMomentumTolerance <= 0. || !std::isfinite(maxStep) ||
      maxStep <= 0.)
    throw std::invalid_argument(
        "Propagation tolerances and step must be finite and positive");
  fPositionTolerance = positionTolerance;
  fMomentumTolerance = relativeMomentumTolerance;
  fMaxStep = maxStep;
  fTrajectory.clear();
}

double MagneticTrackPropagator::GetPlaneZ(const char* volumeName) const {
  double z;
  if (!volumeName || !fGeometry || !fGeometry->GetTopNode() ||
      !FindVolume(fGeometry->GetTopNode(), TGeoHMatrix(), volumeName, z))
    throw std::runtime_error("Detector plane volume not found in geometry");
  return z;
}

std::pair<double, double> MagneticTrackPropagator::GetVolumeZRange(
    const char* volumeName) const {
  std::pair<double, double> range;
  if (!volumeName || !fGeometry || !fGeometry->GetTopNode() ||
      !FindVolumeRange(fGeometry->GetTopNode(), TGeoHMatrix(), volumeName,
                       range))
    throw std::runtime_error(
        std::string("Volume z range not found in geometry: ") +
        (volumeName ? volumeName : "null"));
  return range;
}

std::array<double, 4> MagneticTrackPropagator::GetVolumeExitFaceXY(
    const char* volumeName) const {
  std::array<double, 4> bounds;
  if (!volumeName || !fGeometry || !fGeometry->GetTopNode() ||
      !FindVolumeExitFaceXY(fGeometry->GetTopNode(), TGeoHMatrix(), volumeName,
                            bounds))
    throw std::runtime_error(
        std::string("Volume exit face not found in geometry: ") +
        (volumeName ? volumeName : "null"));
  return bounds;
}

bool MagneticTrackPropagator::InsideBox(const XYZPoint& position,
                                        const Box& box) {
  const auto point = Coordinates(position);
  for (int axis = 0; axis < 3; ++axis)
    if (point[axis] < box.minimum[axis] || point[axis] > box.maximum[axis])
      return false;
  return true;
}

bool MagneticTrackPropagator::SegmentIntersectsBox(const State& start,
                                                   const State& end,
                                                   const Box& box) {
  const double dz = end.position.Z() - start.position.Z();
  if (dz == 0.) return InsideBox(start.position, box);
  const double t1 = (box.minimum[2] - start.position.Z()) / dz;
  const double t2 = (box.maximum[2] - start.position.Z()) / dz;
  const double lo = std::max(0., std::min(t1, t2)),
               hi = std::min(1., std::max(t1, t2));
  if (lo > hi) return false;
  // The same cubic Hermite curve used by PositionAt. Solve for crossings of
  // all four side faces, including curved tracks whose endpoints both miss.
  const auto startPosition = Coordinates(start.position),
             endPosition = Coordinates(end.position),
             startMomentum = Coordinates(start.momentum),
             endMomentum = Coordinates(end.momentum);
  double coefficients[2][4];
  std::vector<double> candidates{lo, hi};
  for (int axis = 0; axis < 2; ++axis) {
    const double a = startPosition[axis], b = endPosition[axis];
    const double da = dz * startMomentum[axis] / start.momentum.Z();
    const double db = dz * endMomentum[axis] / end.momentum.Z();
    auto& c = coefficients[axis];
    c[0] = a;
    c[1] = da;
    c[2] = 3. * (b - a) - 2. * da - db;
    c[3] = 2. * (a - b) + da + db;
    const auto value = [&c](double t) {
      return ((c[3] * t + c[2]) * t + c[1]) * t + c[0];
    };
    std::vector<double> knots{lo, hi};
    const auto addKnot = [&knots, lo, hi](double t) {
      if (t > lo && t < hi) knots.push_back(t);
    };
    // Split at derivative roots, so each interval is monotonic for bisection.
    if (c[3] == 0.) {
      if (c[2] != 0.) addKnot(-c[1] / (2. * c[2]));
    } else {
      const double discriminant = 4. * c[2] * c[2] - 12. * c[3] * c[1];
      if (discriminant >= 0.) {
        addKnot((-2. * c[2] - std::sqrt(discriminant)) / (6. * c[3]));
        addKnot((-2. * c[2] + std::sqrt(discriminant)) / (6. * c[3]));
      }
    }
    std::sort(knots.begin(), knots.end());
    candidates.insert(candidates.end(), knots.begin(), knots.end());
    for (double face : {box.minimum[axis], box.maximum[axis]}) {
      for (std::size_t i = 1; i < knots.size(); ++i) {
        double left = knots[i - 1], right = knots[i];
        double fleft = value(left) - face, fright = value(right) - face;
        if ((fleft < 0. && fright > 0.) || (fleft > 0. && fright < 0.)) {
          for (int iteration = 0; iteration < 50; ++iteration) {
            const double middle = (left + right) / 2.,
                         fmiddle = value(middle) - face;
            if ((fleft < 0.) == (fmiddle < 0.)) {
              left = middle;
              fleft = fmiddle;
            } else
              right = middle;
          }
          candidates.push_back((left + right) / 2.);
        }
      }
    }
  }
  const auto inside = [&coefficients, &box](double t) {
    for (int axis = 0; axis < 2; ++axis) {
      const auto& c = coefficients[axis];
      const double value = ((c[3] * t + c[2]) * t + c[1]) * t + c[0];
      if (value < box.minimum[axis] - 1.e-9 ||
          value > box.maximum[axis] + 1.e-9)
        return false;
    }
    return true;
  };
  std::sort(candidates.begin(), candidates.end());
  for (std::size_t i = 0; i < candidates.size(); ++i) {
    if (inside(candidates[i])) return true;
    if (i && inside((candidates[i - 1] + candidates[i]) / 2.)) return true;
  }
  return false;
}

bool MagneticTrackPropagator::IntersectsBox(double charge,
                                            const XYZPoint& position,
                                            const XYZVector& momentum,
                                            const XYZPoint& minimum,
                                            const XYZPoint& maximum) const {
  if (!Finite(position) || !Finite(momentum) || !Finite(minimum) ||
      !Finite(maximum) || !std::isfinite(charge) ||
      !std::isfinite(momentum.R()) || momentum.R() <= 0.)
    return false;
  const Box box{Coordinates(minimum), Coordinates(maximum)};
  for (int axis = 0; axis < 3; ++axis)
    if (box.minimum[axis] >= box.maximum[axis])
      throw std::invalid_argument("Invalid detector box extent");
  if (InsideBox(position, box)) return true;
  if (charge != 0.) EnsureMuonShield(std::min(position.Z(), minimum.Z()));
  const bool zeroField =
      std::all_of(fFields.begin(), fFields.end(), [&](const auto& map) {
        return std::none_of(
            map.regions.begin(), map.regions.end(), [&](const auto& region) {
              double entry, exit;
              return RayBoxInterval(position, momentum, region, entry, exit);
            });
      });
  if (charge == 0. || zeroField) {
    double entry, exit;
    return RayBoxInterval(position, momentum, box, entry, exit);
  }
  const double z = momentum.Z() >= 0. ? maximum.Z() : minimum.Z();
  if ((z - position.Z()) * momentum.Z() < 0.) return false;
  State result;
  return Propagate(charge, position, momentum, z, result, nullptr, &box);
}

bool MagneticTrackPropagator::RayBoxInterval(const XYZPoint& position,
                                             const XYZVector& direction,
                                             const Box& box, double& entry,
                                             double& exit) {
  const auto point = Coordinates(position), step = Coordinates(direction);
  entry = 0.;
  exit = std::numeric_limits<double>::infinity();
  for (int axis = 0; axis < 3; ++axis) {
    if (step[axis] == 0.) {
      if (point[axis] < box.minimum[axis] || point[axis] > box.maximum[axis])
        return false;
    } else {
      const double a = (box.minimum[axis] - point[axis]) / step[axis];
      const double b = (box.maximum[axis] - point[axis]) / step[axis];
      entry = std::max(entry, std::min(a, b));
      exit = std::min(exit, std::max(a, b));
    }
  }
  return entry <= exit;
}

void MagneticTrackPropagator::SetMuonShieldMinZ(double minimumZ) {
  if (std::isnan(minimumZ) ||
      minimumZ == std::numeric_limits<double>::infinity())
    throw std::invalid_argument("Invalid muon shield minimum z");
  if (fMuonShieldReady) fFields.pop_back();
  fMuonShieldReady = false;
  fMuonShieldMinZ = minimumZ;
  fTrajectory.clear();
}

void MagneticTrackPropagator::EnsureMuonShield(double minimumZ) const {
  if (!fMuonShieldField) return;
  // Reused propagators and backward tracks can request an earlier range.
  if (minimumZ < fMuonShieldMinZ) {
    if (fMuonShieldReady) fFields.pop_back();
    fMuonShieldReady = false;
    fMuonShieldMinZ = minimumZ;
  }
  if (!fMuonShieldReady) {
    AddFieldMap(fMuonShieldField, fMuonShieldMinZ);
    fMuonShieldReady = true;
  }
}

void MagneticTrackPropagator::AddFieldMap(ShipBFieldMap* field,
                                          double minimumZ) const {
  if (!field) return;
  const auto* data = field->getFieldMap();
  const int nx = field->GetNx(), ny = field->GetNy(), nz = field->GetNz();
  if (nx < 2 || ny < 2 || nz < 2 || !data ||
      data->size() != std::size_t(nx) * ny * nz || !(field->GetdX() > 0.) ||
      !(field->GetdY() > 0.) || !(field->GetdZ() > 0.))
    throw std::invalid_argument("Invalid magnetic field grid");
  FieldMap map{
      field,
      {},
      0.5 * std::min({field->GetdX(), field->GetdY(), field->GetdZ()})};
  TGeoTranslation translation(field->GetXOffset(), field->GetYOffset(),
                              field->GetZOffset());
  TGeoRotation rotation("propagationRotation", field->GetPhi(),
                        field->GetTheta(), field->GetPsi());
  TGeoCombiTrans transform(translation, rotation);
  const double xmin =
      field->HasSymmetry() ? -field->GetXMax() : field->GetXMin();
  const double ymin =
      field->HasSymmetry() ? -field->GetYMax() : field->GetYMin();
  // Each nonzero node contributes to both neighbouring interpolation cells.
  // Transform all corners, retaining a conservative 3D envelope for rotations
  // and quadrant symmetry. Skip reading layers wholly below the input range.
  for (int iz = 0; iz < nz; ++iz) {
    const double zlo = field->GetZMin() + std::max(0, iz - 1) * field->GetdZ();
    const double zhi =
        field->GetZMin() + std::min(nz - 1, iz + 1) * field->GetdZ();
    const double inf = std::numeric_limits<double>::infinity();
    Box region{{inf, inf, inf}, {-inf, -inf, -inf}};
    for (double x : {xmin, static_cast<double>(field->GetXMax())})
      for (double y : {ymin, static_cast<double>(field->GetYMax())})
        for (double z : {zlo, zhi}) {
          const double local[3] = {x, y, z};
          double global[3];
          transform.LocalToMaster(local, global);
          for (int axis = 0; axis < 3; ++axis) {
            region.minimum[axis] = std::min(region.minimum[axis], global[axis]);
            region.maximum[axis] = std::max(region.maximum[axis], global[axis]);
          }
        }
    if (region.maximum[2] < minimumZ) continue;
    bool active = false;
    for (int ix = 0; ix < nx; ++ix)
      for (int iy = 0; iy < ny; ++iy) {
        const auto& b = data->at((std::size_t(ix) * ny + iy) * nz + iz);
        if (!std::isfinite(b[0]) || !std::isfinite(b[1]) ||
            !std::isfinite(b[2]))
          throw std::invalid_argument("Non-finite magnetic field value");
        active = active || b[0] != 0. || b[1] != 0. || b[2] != 0.;
      }
    if (!active) continue;
    region.minimum[2] = std::max(region.minimum[2], minimumZ);
    map.regions.push_back(region);
  }
  std::sort(
      map.regions.begin(), map.regions.end(),
      [](const Box& a, const Box& b) { return a.minimum[2] < b.minimum[2]; });
  std::vector<Box> merged;
  for (const auto& region : map.regions) {
    if (!merged.empty() && region.minimum[2] <= merged.back().maximum[2]) {
      for (int axis = 0; axis < 3; ++axis) {
        merged.back().minimum[axis] =
            std::min(merged.back().minimum[axis], region.minimum[axis]);
        merged.back().maximum[axis] =
            std::max(merged.back().maximum[axis], region.maximum[axis]);
      }
    } else
      merged.push_back(region);
  }
  map.regions.swap(merged);
  fFields.push_back(std::move(map));
}

bool MagneticTrackPropagator::Derivative(const State& state, double charge,
                                         double pzSign,
                                         StateDerivative& derivative) const {
  if (!Finite(state.position) || !Finite(state.momentum) ||
      state.momentum.Z() * pzSign <= 1.e-10 * state.momentum.R())
    return false;
  const double point[3] = {state.position.X(), state.position.Y(),
                           state.position.Z()};
  double b[3] = {0., 0., 0.};
  for (const auto& map : fFields) {
    if (std::none_of(map.regions.begin(), map.regions.end(),
                     [&state](const auto& region) {
                       return InsideBox(state.position, region);
                     }))
      continue;
    double component[3] = {0., 0., 0.};
    map.field->Field(point, component);
    for (int i = 0; i < 3; ++i) b[i] += component[i];
  }
  derivative.slope = state.momentum * (1. / state.momentum.Z());
  // dp/dz = 0.000299792458 q (p cross B)/pz for cm, GeV/c and kGauss.
  derivative.momentum = state.momentum.Cross(XYZVector(b[0], b[1], b[2])) *
                        (0.000299792458 * charge / state.momentum.Z());
  return Finite(derivative.slope) && Finite(derivative.momentum);
}

bool MagneticTrackPropagator::RKStep(const State& state, double charge,
                                     double pzSign, double dz,
                                     State& result) const {
  const auto advance = [](const State& a, const StateDerivative& b,
                          double step) {
    return State{a.position + step * b.slope, a.momentum + step * b.momentum};
  };
  StateDerivative k1, k2, k3, k4;
  if (!Derivative(state, charge, pzSign, k1) ||
      !Derivative(advance(state, k1, dz / 2.), charge, pzSign, k2) ||
      !Derivative(advance(state, k2, dz / 2.), charge, pzSign, k3) ||
      !Derivative(advance(state, k3, dz), charge, pzSign, k4))
    return false;
  result.position = state.position + (dz / 6.) * (k1.slope + 2. * k2.slope +
                                                  2. * k3.slope + k4.slope);
  result.momentum =
      state.momentum + (dz / 6.) * (k1.momentum + 2. * k2.momentum +
                                    2. * k3.momentum + k4.momentum);
  result.position.SetZ(state.position.Z() + dz);
  return Finite(result.position) && Finite(result.momentum) &&
         result.momentum.Z() * pzSign > 1.e-10 * result.momentum.R();
}

bool MagneticTrackPropagator::Propagate(double charge, const XYZPoint& position,
                                        const XYZVector& momentum, double z,
                                        State& result,
                                        std::vector<State>* trajectory,
                                        const Box* box) const {
  if (!Finite(position) || !Finite(momentum) || !std::isfinite(z) ||
      !std::isfinite(charge) || !std::isfinite(momentum.R()) ||
      momentum.R() <= 0.)
    return false;
  if (charge != 0.) EnsureMuonShield(std::min(position.Z(), z));
  result = {position, momentum};
  if (trajectory) trajectory->push_back(result);
  if (box && InsideBox(position, *box)) return true;
  if (z == position.Z()) return box == nullptr;
  const double p = momentum.R(), pzSign = momentum.Z() >= 0. ? 1. : -1.;
  if (std::abs(momentum.Z()) <= 1.e-10 * p) return false;
  const double direction = z > position.Z() ? 1. : -1.;
  double nextStep = fMaxStep;
  for (unsigned step = 0; step < 100000; ++step) {
    const double currentZ = result.position.Z();
    if (currentZ == z) return box == nullptr;
    const State previous = result;
    double boundary = z;
    bool inField = false;
    double gridStep = fMaxStep;
    if (charge != 0.) {
      for (const auto& map : fFields) {
        for (const auto& region : map.regions) {
          double entry, exit;
          const XYZVector travel =
              (direction / result.momentum.Z()) * result.momentum;
          if (!RayBoxInterval(result.position, travel, region, entry, exit) ||
              exit <= 0.)
            continue;
          if (entry <= 1.e-7) {
            inField = true;
            gridStep = std::min(gridStep, map.gridStep);
            const double leave =
                direction > 0. ? region.maximum[2] : region.minimum[2];
            if (direction * (leave - boundary) < 0.) boundary = leave;
          } else if (entry < direction * (boundary - currentZ)) {
            boundary = currentZ + direction * entry;
          }
        }
      }
    }
    if (!inField) {
      result.position +=
          ((boundary - currentZ) / result.momentum.Z()) * result.momentum;
      result.position.SetZ(boundary);
      if (!Finite(result.position)) return false;
    } else {
      double dz =
          direction * std::min({std::abs(boundary - currentZ), nextStep,
                                gridStep * std::abs(result.momentum.Z()) / p});
      State full, half, fine;
      bool accepted = false;
      for (int retry = 0; retry < 40; ++retry) {
        if (std::abs(dz) < 1.e-8 || currentZ + dz == currentZ) return false;
        if (RKStep(result, charge, pzSign, dz, full) &&
            RKStep(result, charge, pzSign, dz / 2., half) &&
            RKStep(half, charge, pzSign, dz / 2., fine)) {
          const double error = std::max(
              (fine.position - full.position).R() / fPositionTolerance,
              (fine.momentum - full.momentum).R() / (fMomentumTolerance * p));
          if (error <= 1.) {
            fine.momentum *= p / fine.momentum.R();
            fine.position.SetZ(currentZ + dz);
            result = fine;
            nextStep = std::abs(dz) * (error < 0.03 ? 2. : 1.);
            accepted = true;
            break;
          }
        }
        dz *= 0.5;
      }
      if (!accepted) return false;
    }
    if (box && SegmentIntersectsBox(previous, result, *box)) return true;
    if (trajectory) trajectory->push_back(result);
  }
  return false;
}

bool MagneticTrackPropagator::Extrapolate(double charge,
                                          const XYZPoint& position,
                                          const XYZVector& momentum, double z,
                                          XYZPoint& result,
                                          XYZVector& resultMomentum) const {
  State end;
  if (!Propagate(charge, position, momentum, z, end, nullptr)) return false;
  result = end.position;
  resultMomentum = end.momentum;
  return true;
}

bool MagneticTrackPropagator::BuildTrajectory(double charge,
                                              const XYZPoint& position,
                                              const XYZVector& momentum,
                                              double endZ) {
  fTrajectory.clear();
  State end;
  if (!Propagate(charge, position, momentum, endZ, end, &fTrajectory)) {
    fTrajectory.clear();
    return false;
  }
  if (endZ < position.Z()) std::reverse(fTrajectory.begin(), fTrajectory.end());
  return true;
}

bool MagneticTrackPropagator::PositionAt(double z, XYZPoint& position) const {
  if (!std::isfinite(z) || fTrajectory.empty() ||
      z < fTrajectory.front().position.Z() ||
      z > fTrajectory.back().position.Z())
    return false;
  const auto upper = std::lower_bound(fTrajectory.begin(), fTrajectory.end(), z,
                                      [](const State& state, double value) {
                                        return state.position.Z() < value;
                                      });
  if (upper->position.Z() == z) {
    position = upper->position;
    return true;
  }
  const auto& a = *(upper - 1);
  const auto& b = *upper;
  const double dz = b.position.Z() - a.position.Z(),
               t = (z - a.position.Z()) / dz;
  // Cubic Hermite basis; h00 + h01 = 1, so the points enter as a + h01 (b - a).
  position = a.position +
             (-2 * t * t * t + 3 * t * t) * (b.position - a.position) +
             (t * t * t - 2 * t * t + t) * dz / a.momentum.Z() * a.momentum +
             (t * t * t - t * t) * dz / b.momentum.Z() * b.momentum;
  position.SetZ(z);
  return Finite(position);
}

bool MagneticTrackPropagator::GetTrajectoryState(std::size_t index,
                                                 XYZPoint& position,
                                                 XYZVector& momentum) const {
  if (index >= fTrajectory.size()) return false;
  position = fTrajectory[index].position;
  momentum = fTrajectory[index].momentum;
  return true;
}

double MagneticTrackPropagator::GetFieldEndZ(double minimumZ) const {
  if (!std::isfinite(minimumZ))
    throw std::invalid_argument("Field extent requires a finite minimum z");
  EnsureMuonShield(minimumZ);
  double end = minimumZ;
  for (const auto& map : fFields)
    for (const auto& region : map.regions)
      end = std::max(end, region.maximum[2]);
  return end;
}

bool MagneticTrackPropagator::HasFieldAt(const XYZPoint& position) const {
  if (!Finite(position))
    throw std::invalid_argument("Field query requires a finite position");
  EnsureMuonShield(position.Z());
  const double point[3] = {position.X(), position.Y(), position.Z()};
  XYZVector field;
  for (const auto& map : fFields) {
    double component[3] = {0., 0., 0.};
    map.field->Field(point, component);
    field += XYZVector(component[0], component[1], component[2]);
  }
  return field.Mag2() != 0.;
}
