// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "MuGeoProcessor.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <functional>
#include <limits>
#include <stdexcept>
#include <utility>

#include "TGeoBBox.h"

using namespace ShipMuDIS;

MuGeoProcessor::MuGeoProcessor() {
  fZmax = 14000;
  fZmin = 2500;
}

/** destructor **/
MuGeoProcessor::~MuGeoProcessor() = default;

void MuGeoProcessor::SetMuonShieldField(ShipBFieldMap* field,
                                        TGeoManager* geometry) {
  if (!field || !geometry || geometry != gGeoManager)
    throw std::invalid_argument(
        "Shield transport requires a map and the active geometry");
  fPropagator =
      std::make_unique<MagneticTrackPropagator>(nullptr, geometry, field);
  fPropagator->SetAccuracy(1.e-4, 1.e-7, 0.5);
  fGeometry = nullptr;
  fTopNode = nullptr;
  CacheGeometry();
}

void MuGeoProcessor::CacheGeometry() {
  if (!gGeoManager || !gGeoManager->GetTopNode())
    throw std::runtime_error("Muon path discovery requires a closed geometry");
  if (fGeometry == gGeoManager && fTopNode == gGeoManager->GetTopNode()) return;
  if (fGeometry && fGeometry != gGeoManager && fPropagator)
    throw std::runtime_error(
        "Configure the shield field again after changing geometry");
  fGeometry = gGeoManager;
  fTopNode = gGeoManager->GetTopNode();
  fShieldVolumes.clear();
  fShieldMinZ = std::numeric_limits<double>::infinity();
  std::function<void(TGeoNode*, const TGeoHMatrix&, bool)> visit;
  visit = [&](TGeoNode* node, const TGeoHMatrix& parent, bool inShield) {
    TGeoHMatrix transform(parent);
    transform.Multiply(node->GetMatrix());
    auto* volume = node->GetVolume();
    const std::string name = volume->GetName();
    inShield = inShield || name == "MuonShieldArea";
    if (inShield && name.find("Magn") != std::string::npos &&
        !volume->IsAssembly()) {
      fShieldVolumes.insert(volume);
      // Geometry is used only for material navigation and the upstream
      // stopping plane, never to decide whether a track needs bending.
      auto* box = dynamic_cast<TGeoBBox*>(volume->GetShape());
      if (!box)
        throw std::runtime_error("Shield magnet has no bounding box: " + name);
      box->ComputeBBox();
      const auto* origin = box->GetOrigin();
      for (double x : {-box->GetDX(), box->GetDX()})
        for (double y : {-box->GetDY(), box->GetDY()})
          for (double z : {-box->GetDZ(), box->GetDZ()}) {
            const double local[3] = {origin[0] + x, origin[1] + y,
                                     origin[2] + z};
            double global[3];
            transform.LocalToMaster(local, global);
            fShieldMinZ = std::min(fShieldMinZ, global[2]);
          }
    }
    for (int i = 0; i < node->GetNdaughters(); ++i)
      visit(node->GetDaughter(i), transform, inShield);
  };
  visit(fTopNode, TGeoHMatrix(), false);
}

bool MuGeoProcessor::AddMagneticChord(const TVector3& a, const TVector3& b,
                                      double momentum, double& time,
                                      unsigned depth) {
  double error = 0.;
  TVector3 middle;
  for (double fraction : {0.25, 0.5, 0.75}) {
    TVector3 point;
    if (!fPropagator->PositionAt(a.Z() + fraction * (b.Z() - a.Z()), point))
      return false;
    error = std::max(error, (point - (a + fraction * (b - a))).Mag());
    if (fraction == 0.5) middle = point;
  }
  if (error > 1.e-4) {
    if (depth == 30) return false;
    return AddMagneticChord(a, middle, momentum, time, depth + 1) &&
           AddMagneticChord(middle, b, momentum, time, depth + 1);
  }
  const TVector3 displacement = b - a;
  fSegments.push_back(
      {{a, momentum * displacement.Unit(), time}, a.Z(), b.Z(), false});
  const double speed = c_light * momentum / std::hypot(momentum, muon_mass);
  time += displacement.Mag() / speed;
  return true;
}

bool MuGeoProcessor::AddMagneticSegments(const Measurement& start,
                                         double charge, double endZ) {
  if (!fPropagator->BuildTrajectory(charge, start.position, start.momentum,
                                    endZ))
    return false;
  double time = start.time;
  TVector3 previous = start.position, position, momentum;
  for (std::size_t i = 1; i < fPropagator->GetTrajectorySize(); ++i) {
    if (!fPropagator->GetTrajectoryState(i, position, momentum) ||
        !AddMagneticChord(previous, position, start.momentum.Mag(), time))
      return false;
    previous = position;
  }
  return true;
}

double MuGeoProcessor::GetTrajectoryPocaZ(const Measurement& hit) const {
  if (fSegments.empty()) return fStart.position.Z();
  const TVector3 direction = hit.momentum.Unit();
  double bestDistance = std::numeric_limits<double>::infinity();
  double pocaZ = fStart.position.Z();
  // Minimize the distance between each refined trajectory chord and the
  // hit's line. Use the midpoint of the closest pair, as in GetVertex().
  for (const auto& segment : fSegments) {
    const auto& m = segment.measurement;
    const TVector3 delta = m.position - hit.position;
    const TVector3 slope = m.momentum * (1. / m.momentum.Z());
    const TVector3 transverse = slope - slope.Dot(direction) * direction;
    const double denominator = transverse.Mag2();
    const double dz = denominator < 1.e-12
                          ? 0.
                          : std::clamp(-delta.Dot(transverse) / denominator, 0.,
                                       segment.endZ - segment.startZ);
    const TVector3 onTrack = m.position + dz * slope;
    const TVector3 onLine =
        hit.position + (onTrack - hit.position).Dot(direction) * direction;
    const double distance = (onTrack - onLine).Mag2();
    if (distance < bestDistance) {
      bestDistance = distance;
      pocaZ =
          denominator < 1.e-12 ? onTrack.Z() : 0.5 * (onTrack.Z() + onLine.Z());
    }
  }
  return std::clamp(pocaZ, fStart.position.Z(), fSegments.back().endZ);
}

void MuGeoProcessor::SetPocaJumpThreshold(double threshold) {
  if (!std::isfinite(threshold) || threshold < 0.)
    throw std::invalid_argument(
        "POCA jump threshold must be finite and nonnegative");
  fPocaJumpThreshold = threshold;
}

void MuGeoProcessor::ResetDiagnostics() {
  fMuons = fBackwardMuons = fInvalidMuons = fTransitions = 0;
  fUBTBackwardPaths = fStartMagneticPaths = fStartStraightPaths = 0;
  fUBTBackwardMisses = fStartsBeyondZmax = fStartsBeforeZmin = 0;
  fLargeJumps = fMuonsWithLargeJumps = 0;
  fMaxTransverseJump = 0.;
}

void MuGeoProcessor::PrintDiagnostics() const {
  LOG(info) << "Muon path diagnostics: " << fMuons << " muons considered, "
            << fBackwardMuons << " rejected for non-forward momentum, "
            << fInvalidMuons << " rejected for invalid measurements";
  LOG(info) << "Muon path routes prepared (before material navigation): "
            << fUBTBackwardPaths << " from UBT with backward extrapolation, "
            << fStartMagneticPaths << " from MC start in field, "
            << fStartStraightPaths
            << " from MC start in field-free region (bending on field entry); "
            << fStartsBeyondZmax << " skipped with start z >= maximum z";
  LOG(info) << "UBT backward paths missing MS: " << fUBTBackwardMisses;
  LOG(info) << "Muons starting before z = " << fZmin
            << " cm (paths still built): " << fStartsBeforeZmin;
  LOG(info) << "POCA transverse jumps: " << fLargeJumps << " of "
            << fTransitions << " transitions exceed " << fPocaJumpThreshold
            << " cm, in " << fMuonsWithLargeJumps
            << " muons; maximum jump = " << fMaxTransverseJump << " cm";
}

bool MuGeoProcessor::initialise(MuonBranches& aEvt) {
  fSegments.clear();
  fTraceBackward = false;
  fPathMap.clear();
  ++fMuons;
  if (aEvt.mcTrks.empty()) {
    ++fInvalidMuons;
    return false;
  }

  std::array<Measurement, 8> measurements;
  unsigned count = 1;
  aEvt.mcTrks[0].GetStartVertex(measurements[0].position);
  aEvt.mcTrks[0].GetMomentum(measurements[0].momentum);
  measurements[0].time = aEvt.mcTrks[0].GetStartT();
  const auto addHit = [&](const auto& hit) {
    auto& measurement = measurements[count++];
    hit.Position(measurement.position);
    hit.Momentum(measurement.momentum);
    measurement.time = hit.GetTime();
  };
  if (!aEvt.ubtPt.empty()) addHit(aEvt.ubtPt.front());
  if (!aEvt.sbtPt.empty()) addHit(aEvt.sbtPt.front());
  std::array<bool, 4> found = {};
  unsigned stations = 0;
  for (const auto& hit : aEvt.sstPt) {
    const int station = hit.GetDetectorID() / 1000000;
    if (station < 1 || station > 4 || found[station - 1]) continue;
    found[station - 1] = true;
    addHit(hit);
    if (++stations == 4) break;
  }
  if (!aEvt.tdPt.empty()) addHit(aEvt.tdPt.front());

  for (unsigned i = 0; i < count; ++i) {
    const auto& m = measurements[i];
    if (!std::isfinite(m.position.X()) || !std::isfinite(m.position.Y()) ||
        !std::isfinite(m.position.Z()) || !std::isfinite(m.momentum.X()) ||
        !std::isfinite(m.momentum.Y()) || !std::isfinite(m.momentum.Z()) ||
        !std::isfinite(m.momentum.Mag()) || !std::isfinite(m.time) ||
        m.momentum.Mag() == 0.) {
      ++fInvalidMuons;
      return false;
    }
    if (m.momentum.Z() <= 0.) {
      ++fBackwardMuons;
      return false;
    }
    if (m.position.Z() < measurements[0].position.Z()) {
      ++fInvalidMuons;
      return false;
    }
  }
  // Stable insertion sort for at most seven hits, without allocating storage.
  for (unsigned i = 2; i < count; ++i) {
    const auto measurement = measurements[i];
    unsigned j = i;
    while (j > 1 &&
           measurements[j - 1].position.Z() > measurement.position.Z()) {
      measurements[j] = measurements[j - 1];
      --j;
    }
    measurements[j] = measurement;
  }

  CacheGeometry();
  fStart = measurements[0];
  if (fStart.position.Z() >= fZmax) {
    ++fStartsBeyondZmax;
    return true;
  }
  const bool hasUBT = !aEvt.ubtPt.empty();
  if (hasUBT) {
    aEvt.ubtPt.front().Position(fUBT.position);
    aEvt.ubtPt.front().Momentum(fUBT.momentum);
    fUBT.time = aEvt.ubtPt.front().GetTime();
  }
  double startZ = fStart.position.Z();
  unsigned first = 0;
  if (hasUBT) {
    fTraceBackward = true;
    // UBT always anchors both legs, irrespective of the MC start or field.
    unsigned kept = 1;
    for (unsigned i = 1; i < count; ++i)
      if (measurements[i].position.Z() > fUBT.position.Z())
        measurements[kept++] = measurements[i];
    measurements[0] = fUBT;
    count = kept;
    startZ = fUBT.position.Z();
    ++fUBTBackwardPaths;
  } else if (fPropagator) {
    const bool startsInField = fPropagator->HasFieldAt(fStart.position);
    // The propagator skips field-free regions linearly and resumes bending
    // whenever the line enters a nonzero map region, including fringes.
    const double endZ =
        count > 1 ? std::min(fZmax, measurements[1].position.Z()) : fZmax;
    const double charge = aEvt.mcTrks[0].GetPdgCode() == 13 ? -1. : 1.;
    if (!AddMagneticSegments(fStart, charge, endZ)) {
      LOG(error) << "Muon shield magnetic propagation failed at start z = "
                 << startZ;
      fSegments.clear();
      ++fInvalidMuons;
      return false;
    }
    startZ = count > 1 ? GetTrajectoryPocaZ(measurements[1]) : endZ;
    // Keep only the trajectory before the switching plane. The first
    // detector line takes over there, including a POCA inside the field.
    while (!fSegments.empty() && fSegments.back().startZ >= startZ)
      fSegments.pop_back();
    if (fSegments.empty())
      fSegments.push_back({fStart, startZ, startZ, false});
    else
      fSegments.back().endZ = startZ;
    first = 1;
    if (startsInField)
      ++fStartMagneticPaths;
    else
      ++fStartStraightPaths;
  } else {
    if (!fShieldVolumes.empty())
      throw std::runtime_error(
          "Muon without UBT requires a configured shield field map");
    ++fStartStraightPaths;
  }
  for (unsigned i = first; i < count && startZ < fZmax; ++i) {
    const auto& m = measurements[i];
    const double pocaZ =
        i + 1 < count ? std::min(fZmax, GetVertex(m.position, m.momentum,
                                                  measurements[i + 1].position,
                                                  measurements[i + 1].momentum)
                                            .Z())
                      : fZmax;
    // Switching planes must remain ordered to avoid replaying material.
    const double endZ = std::max(startZ, pocaZ);
    fSegments.push_back({m, startZ, endZ, i > 0});
    startZ = endZ;
  }
  return true;
}

TVector3 MuGeoProcessor::GetVertex(const TVector3& r1, const TVector3& p1,
                                   const TVector3& r2, const TVector3& p2) {
  TVector3 u1 = p1.Unit();
  TVector3 u2 = p2.Unit();

  TVector3 w0 = r1 - r2;

  double a = u1 * u1;
  double b = u1 * u2;
  double c = u2 * u2;

  double d = u1 * w0;
  double e = u2 * w0;

  double denom = a * c - b * b;

  // Protect against nearly parallel tracks
  if (std::abs(denom) < 1e-12) {
    LOG(debug) << "GetVertex(): nearly parallel tracks (denominator = " << denom
               << "). Returning first measurement.";
    return r1;
  }

  double t = (b * e - c * d) / denom;
  double s = (a * e - b * d) / denom;

  TVector3 poca1 = r1 + t * u1;
  TVector3 poca2 = r2 + s * u2;

  TVector3 vertex = 0.5 * (poca1 + poca2);

  double zmin = std::min(r1.Z(), r2.Z());
  double zmax = std::max(r1.Z(), r2.Z());

  // Clamp the POCA to the measured interval
  if (vertex.Z() < zmin) {
    return (r1.Z() < r2.Z()) ? r1 : r2;
  }

  if (vertex.Z() > zmax) {
    return (r1.Z() > r2.Z()) ? r1 : r2;
  }

  return vertex;
}

void MuGeoProcessor::CheckAllVolumes() {
  std::map<std::string, double> lMap;
  std::map<std::pair<std::string, std::string>, double> volumeMaterials;
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
    return;
  }

  double z = 2000;
  double step = 50;
  double stepd = 0.1;
  int nS = 8;
  int nSD = 10;
  for (int ix(-nS); ix < nS + 1; ++ix) {
    for (int iy(-nS); iy < nS + 1; ++iy) {
      for (int idx(-nSD); idx < nSD + 1; ++idx) {
        for (int idy(-nSD); idy < nSD + 1; ++idy) {
          if (pow(idx * stepd, 2) + pow(idy * stepd, 2) > 1) continue;
          double dz = sqrt(1 - pow(idx * stepd, 2) - pow(idy * stepd, 2));
          TGeoNode* startnode = gGeoManager->InitTrack(
              ix * step, iy * step, z, idx * stepd, idy * stepd, dz);
          if (!startnode) {
            LOG(error) << "Muon start point out of geometry: " << ix * step
                       << " " << iy * step << " " << z << " " << idx * stepd
                       << " " << idy * stepd << " " << dz;
            continue;
          }
          TGeoNode* currentnode = gGeoManager->GetCurrentNode();
          double snext = z;
          unsigned lcount = 0;

          while (currentnode) {
            const auto* geoMaterial =
                currentnode->GetVolume()->GetMedium()->GetMaterial();
            std::string material = geoMaterial->GetName();
            std::string volName = currentnode->GetVolume()->GetName();
            volumeMaterials.emplace(std::make_pair(volName, material),
                                    geoMaterial->GetDensity());
            // if (volName.find("Tr2") != volName.npos) break;
            volName.append("_");
            volName.append(material);
            lMap.emplace(volName, snext);
            currentnode = gGeoManager->FindNextBoundaryAndStep();
            snext += gGeoManager->GetStep() * dz;

            // for safety...
            if (lcount > 1000) {
              LOG(info) << "Reached 1000 iterations in checking all volumes, "
                           "stopping there: z="
                        << snext << " cm, x=" << ix * step << " y=" << iy * step
                        << " z=" << z << " dir_x=" << idx * stepd
                        << " dir_y=" << idy * stepd << " dir_z=" << dz;
              break;
            }
            lcount++;
          }
        }
      }
    }
  }

  LOG(info) << " -- All volumes found in geometry: n=" << lMap.size();
  for (auto lele = lMap.begin(); lele != lMap.end(); ++lele) {
    LOG(info) << lele->first << " " << lele->second;
  }

  std::map<std::string, std::ostringstream> categoryOutput;
  MuonPath path;
  for (const auto& entry : volumeMaterials) {
    const auto& volName = entry.first.first;
    const auto& material = entry.first.second;
    categoryOutput[path.GetLabel(volName, material)]
        << "  volume=" << volName << ", material=" << material
        << ", density=" << entry.second << " g/cm^3\n";
  }
  std::ostringstream summary;
  summary << " -- Unique volumes and materials by MatType:\n";
  for (const auto& category : MatTypeStr) {
    summary << "MatType " << category.Data() << ":\n"
            << categoryOutput[category.Data()].str();
  }
  LOG(info) << summary.str();
  std::ofstream output("CheckAllVolumes.txt");
  output << summary.str();
  output.close();
  if (!output) {
    LOG(warning) << "Could not write volume summary to CheckAllVolumes.txt";
  }
}

void MuGeoProcessor::AddPath(const MuonPath& path) {
  auto inserted = fPathMap.emplace(path.GetLabel(), path);
  if (!inserted.second) inserted.first->second.Add(path);
}

bool MuGeoProcessor::Trace(const Measurement& measurement, double startZ,
                           double endZ, bool backward) {
  if (startZ == endZ) return true;
  const TVector3 forward = measurement.momentum.Unit();
  const TVector3 direction = backward ? -forward : forward;
  const TVector3 start =
      measurement.position +
      ((startZ - measurement.position.Z()) / forward.Z()) * forward;
  auto* node =
      gGeoManager->InitTrack(start.X(), start.Y(), start.Z(), direction.X(),
                             direction.Y(), direction.Z());
  std::vector<MuonPath> reverse;
  double shieldZ = 0.;
  bool reachedEnd = false;
  unsigned steps = 0;
  while (node) {
    const auto* point = gGeoManager->GetCurrentPoint();
    const TVector3 current(point[0], point[1], point[2]);
    const double remaining = (endZ - current.Z()) / direction.Z();
    if (remaining <= 1.e-8) {
      reachedEnd = true;
      break;
    }
    if (++steps > 10000) {
      LOG(error) << "Muon geometry stepping did not converge at z = "
                 << current.Z();
      break;
    }
    const auto* volume = node->GetVolume();
    const auto* material = volume->GetMaterial();
    if (!material) break;
    const std::string name = volume->GetName();
    const bool shield = fShieldVolumes.count(volume) != 0;
    double limit = remaining;
    if (backward && shield)
      limit = std::min(limit, (kMuonShieldTailZ - shieldZ) / forward.Z());
    node = gGeoManager->FindNextBoundaryAndStep(limit, kFALSE);
    const double step = std::min(gGeoManager->GetStep(), limit);
    if (!std::isfinite(step) || step < 0.) break;
    if (step > 0.) {
      MuonPath path;
      path.AddVolume(name, material->GetName(), material->GetDensity());
      // Only magnets inside MuonShieldArea belong to the shield category.
      if (path.GetLabel() == "MS" && !shield) path.SetLabel("REST");
      path.SetVertexInfo(measurement.position, measurement.momentum,
                         measurement.time);
      path.SetLength(step, backward ? current + step * direction : current,
                     step * forward.Z());
      fVolMap[path.GetLabel()].insert(name + "_" + material->GetName());
      if (backward)
        reverse.push_back(path);
      else
        AddPath(path);
      if (shield) shieldZ += step * forward.Z();
    }
    if (remaining - step <= 1.e-8 ||
        (backward && shieldZ >= kMuonShieldTailZ - 1.e-8)) {
      reachedEnd = true;
      break;
    }
  }
  // Leaving the world is a valid end of the material path.
  if (!node && gGeoManager->IsOutside()) reachedEnd = true;
  if (reachedEnd)
    for (auto it = reverse.rbegin(); it != reverse.rend(); ++it) AddPath(*it);
  return reachedEnd;
}

std::map<std::string, MuonPath>& MuGeoProcessor::FillMuonPath() {
  fPathMap.clear();
  if (!gGeoManager || (fSegments.empty() && !fTraceBackward)) return fPathMap;
  // Informational only: upstream starts are routed via UBT or field transport.
  if (fStart.position.Z() < fZmin) {
    ++fStartsBeforeZmin;
    LOG(debug) << "Muon starts at z = " << fStart.position.Z()
               << " cm, before z_min = " << fZmin << " cm";
  }

  if (fTraceBackward) {
    const double high = std::min(fUBT.position.Z(), fZmax);
    const double low = std::isfinite(fShieldMinZ) ? fShieldMinZ : fZmin;
    if (high > low && !Trace(fUBT, high, low, true)) {
      fPathMap.clear();
      return fPathMap;
    }
    if (fPathMap.count("MS") == 0) {
      ++fUBTBackwardMisses;
      LOG(debug)
          << "UBT backward extrapolation does not cross MS: start position ("
          << fStart.position.X() << ", " << fStart.position.Y() << ", "
          << fStart.position.Z() << "), start momentum (" << fStart.momentum.X()
          << ", " << fStart.momentum.Y() << ", " << fStart.momentum.Z()
          << "), UBT position (" << fUBT.position.X() << ", "
          << fUBT.position.Y() << ", " << fUBT.position.Z()
          << "), UBT momentum (" << fUBT.momentum.X() << ", "
          << fUBT.momentum.Y() << ", " << fUBT.momentum.Z() << "), start time "
          << fStart.time << ", UBT time " << fUBT.time;
    }
  }

  bool hasPrevious = false;
  bool hasLargeJump = false;
  TVector3 previousEnd;
  for (const auto& segment : fSegments) {
    const auto& m = segment.measurement;
    const TVector3 direction = m.momentum.Unit();
    const TVector3 start =
        m.position +
        ((segment.startZ - m.position.Z()) / direction.Z()) * direction;
    if (hasPrevious && segment.measurementTransition) {
      const double jump = (start - previousEnd).Perp();
      ++fTransitions;
      fMaxTransverseJump = std::max(fMaxTransverseJump, jump);
      if (jump > fPocaJumpThreshold) {
        ++fLargeJumps;
        hasLargeJump = true;
      }
    }
    if (!Trace(m, segment.startZ, segment.endZ)) {
      fPathMap.clear();
      return fPathMap;
    }
    previousEnd = m.position +
                  ((segment.endZ - m.position.Z()) / direction.Z()) * direction;
    hasPrevious = true;
  }
  if (hasLargeJump) ++fMuonsWithLargeJumps;
  return fPathMap;
}

void MuGeoProcessor::PrintVolumes() {
  LOG(info) << " -- Volume Map elements: size=" << fVolMap.size();
  for (const auto& [label, volumes] : fVolMap) {
    LOG(info) << label << ":";
    for (const auto& volume : volumes) {
      LOG(info) << "  " << volume;
    }
  }
}
