// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#include "MuGeoProcessor.h"

#include <cmath>
#include <fstream>
#include <stdexcept>
#include <utility>

using namespace ShipMuDIS;

MuGeoProcessor::MuGeoProcessor() {
  fZmax = 14000;
  fZmin = 2500;
}

/** destructor **/
MuGeoProcessor::~MuGeoProcessor() = default;

void MuGeoProcessor::SetPocaJumpThreshold(double threshold) {
  if (!std::isfinite(threshold) || threshold < 0.)
    throw std::invalid_argument("POCA jump threshold must be finite and nonnegative");
  fPocaJumpThreshold = threshold;
}

void MuGeoProcessor::ResetDiagnostics() {
  fMuons = fBackwardMuons = fInvalidMuons = fTransitions = 0;
  fLargeJumps = fMuonsWithLargeJumps = 0;
  fMaxTransverseJump = 0.;
}

void MuGeoProcessor::PrintDiagnostics() const {
  LOG(info) << "Muon path diagnostics: " << fMuons << " muons considered, "
            << fBackwardMuons << " rejected for non-forward momentum, "
            << fInvalidMuons << " rejected for invalid measurements";
  LOG(info) << "POCA transverse jumps: " << fLargeJumps << " of "
            << fTransitions << " transitions exceed " << fPocaJumpThreshold
            << " cm, in " << fMuonsWithLargeJumps << " muons; maximum jump = "
            << fMaxTransverseJump << " cm";
}

bool MuGeoProcessor::initialise(MuonBranches& aEvt) {
  fNSegments = 0;
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
    while (j > 1 && measurements[j - 1].position.Z() > measurement.position.Z()) {
      measurements[j] = measurements[j - 1];
      --j;
    }
    measurements[j] = measurement;
  }

  double startZ = measurements[0].position.Z();
  for (unsigned i = 0; i < count && startZ < fZmax; ++i) {
    const auto& m = measurements[i];
    const double endZ = i + 1 < count
        ? std::min(fZmax, GetVertex(m.position, m.momentum,
                                    measurements[i + 1].position,
                                    measurements[i + 1].momentum).Z())
        : fZmax;
    fSegments[fNSegments++] = {m, startZ, endZ};
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
    LOG(debug) << "GetVertex(): nearly parallel tracks (denominator = "
                 << denom << "). Returning first measurement.";
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

void MuGeoProcessor::FillZmaxVolumes() {
  fZmaxMap.clear();
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
    return;
  }
  double zStart = 400;  // approx. end of HA
  TGeoNode* startnode = gGeoManager->InitTrack(0, 0, zStart, 0, 0, 1);
  if (!startnode) {
    LOG(error) << "Muon start point out of geometry: (0,0," << zStart
               << "), going along z ";
    return;
  }

  TGeoNode* currentnode = gGeoManager->GetCurrentNode();
  std::string volName = currentnode->GetVolume()->GetName();
  double snext = zStart;
  unsigned lcount = 0;
  bool foundMS = false;
  bool foundUBT = false;
  while (currentnode) {
    volName = currentnode->GetVolume()->GetName();
    if (volName.find("Magn") != volName.npos) foundMS = true;
    if (volName.find("Upstream") != volName.npos) foundUBT = true;
    currentnode = gGeoManager->FindNextBoundaryAndStep();

    if (!currentnode) {
      LOG(error) << "Next boundary out of geometry.";
      break;
    }

    snext += gGeoManager->GetStep();
    LOG(info) << "Volume: " << volName << ", end z = " << snext;
    volName = currentnode->GetVolume()->GetName();
    //@FIXME AMM-avoid hardcoding, pass by config ?
    if (foundMS && volName.find("Magn") == volName.npos) {
      LOG(info) << " Found end of magnet at z = " << snext;
      fZmaxMap.emplace("MS", snext);
      foundMS = false;
    }
    if (foundUBT && volName.find("Upstream") == volName.npos) {
      LOG(info) << " Found end of Upstream detector at z = " << snext;
      fZmaxMap.emplace("UBT", snext);
      break;
    }
    // for safety...
    if (lcount > 1000) {
      LOG(info) << "Reached 1000 iterations in checking all volumes, stopping "
                   "there: z="
                << snext;
      break;
    }
    lcount++;
  }

  if (fZmaxMap.size() != 2) {
    LOG(info) << " Warning, map size is : " << fZmaxMap.size()
              << ", did not find the maximum z position of MS and UBT, will be "
                 "using Zmax= "
              << fZmax << " parameter.";
  }
}

void MuGeoProcessor::CheckAllVolumes() {
  std::map<std::string, double> lMap;
  std::map<std::pair<std::string, std::string>, double> volumeMaterials;
  if (!gGeoManager) {
    LOG(error) << "gGeoManager does not exist!";
    return;
  }

  double z = fZmin;
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

std::map<std::string, MuonPath>& MuGeoProcessor::FillMuonPath() {
  fPathMap.clear();
  if (!gGeoManager || fNSegments == 0) return fPathMap;
  if (fSegments[0].startZ < fZmin) {
    LOG(error) << "Muon starts before minimum z = " << fZmin << " cm";
    return fPathMap;
  }

  bool hasPrevious = false;
  bool hasLargeJump = false;
  TVector3 previousEnd;
  for (unsigned i = 0; i < fNSegments; ++i) {
    const auto& segment = fSegments[i];
    const auto& m = segment.measurement;
    const TVector3 direction = m.momentum.Unit();
    // The POCA supplies only the switching z; both lines stay anchored to
    // their own measurements, including backward extrapolation to startZ.
    const TVector3 start = m.position +
        ((segment.startZ - m.position.Z()) / direction.Z()) * direction;
    if (hasPrevious) {
      const double jump = (start - previousEnd).Perp();
      ++fTransitions;
      fMaxTransverseJump = std::max(fMaxTransverseJump, jump);
      if (jump > fPocaJumpThreshold) {
        ++fLargeJumps;
        hasLargeJump = true;
      }
    }

    // A clamped POCA can give a zero-length segment. Keep its switching
    // diagnostic, but do not navigate or assign any material to it.
    if (segment.endZ == segment.startZ) {
      previousEnd = start;
      hasPrevious = true;
      continue;
    }
    TGeoNode* node = gGeoManager->InitTrack(
        start.X(), start.Y(), start.Z(), direction.X(), direction.Y(), direction.Z());
    if (!node) break;

    unsigned steps = 0;
    bool reachedEnd = false;
    while (node) {
      const Double_t* point = gGeoManager->GetCurrentPoint();
      const TVector3 current(point[0], point[1], point[2]);
      const double remaining = (segment.endZ - current.Z()) / direction.Z();
      if (remaining <= 1.e-8) {
        reachedEnd = true;
        break;
      }
      if (++steps > 10000) {
        LOG(error) << "Muon geometry stepping did not converge at z = " << current.Z();
        break;
      }
      const auto* volume = node->GetVolume();
      const auto* material = volume->GetMedium()->GetMaterial();
      const std::string name = volume->GetName();
      node = gGeoManager->FindNextBoundaryAndStep(remaining, kFALSE);
      const double step = std::min(gGeoManager->GetStep(), remaining);
      if (!std::isfinite(step) || step < 0.) break;
      if (step > 0.) {
        MuonPath path;
        path.AddVolume(name, material->GetName(), material->GetDensity());
        path.SetVertexInfo(m.position, m.momentum, m.time);
        path.SetLength(step, current, step * direction.Z());
        fVolMap[path.GetLabel()].insert(name + "_" + material->GetName());
        auto inserted = fPathMap.emplace(path.GetLabel(), path);
        if (!inserted.second) inserted.first->second.Add(path);
      }
      if (remaining - step <= 1.e-8) {
        reachedEnd = true;
        break;
      }
    }
    if (!reachedEnd) break;
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
