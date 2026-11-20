// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Tests of the straw pattern recognition: the sign convention of the drift
// distances against the ACTS straw surface, and finding a synthetic track.

#include <cmath>
#include <iostream>
#include <memory>
#include <vector>

#include "Acts/Geometry/GeometryContext.hpp"
#include "Acts/Surfaces/LineBounds.hpp"
#include "Acts/Surfaces/StrawSurface.hpp"
#include "ActsFrame.hpp"
#include "StrawPatRec.hpp"

namespace {

constexpr double kStereoAngle = 4.57 * M_PI / 180.;
constexpr double kPitch = 2.;   // cm
constexpr double kRadius = 1.;  // cm

int failures = 0;

void check(bool condition, const char* what) {
  if (!condition) {
    std::cout << "FAIL: " << what << std::endl;
    ++failures;
  }
}

SHiP::StrawWire makeWire(int station, int view, int layer, double angle,
                         double offset, double z) {
  // Wires along (cos a, sin a); offset along the normal (-sin a, cos a)
  const double dx = std::cos(angle);
  const double dy = std::sin(angle);
  return SHiP::StrawWire{0, station, view, layer, -dy * offset, dx * offset,
                         z, dx,      dy,   0.,    kRadius,      250.};
}

double viewAngle(int view) {
  return view == 1 ? kStereoAngle : view == 2 ? -kStereoAngle : 0.;
}

/// loc0 of the ACTS straw surface for the track `line` and `wire`, in cm
double actsLoc0(const SHiP::LineSegment& line, const SHiP::StrawWire& wire) {
  const auto gctx = Acts::GeometryContext::dangerouslyDefaultConstruct();
  Acts::Transform3 ship = Acts::Transform3::Identity();
  const Acts::Vector3 axis(wire.dx, wire.dy, wire.dz);
  const Acts::Vector3 other = axis.cross(Acts::Vector3::UnitZ()).normalized();
  ship.linear().col(0) = other;
  ship.linear().col(1) = axis.cross(other);
  ship.linear().col(2) = axis;
  ship.translation() = Acts::Vector3(wire.x, wire.y, wire.z);
  const auto surface = Acts::Surface::makeShared<Acts::StrawSurface>(
      SHiP::ActsFrame::transformToActs(ship),
      std::make_shared<const Acts::LineBounds>(kRadius * 10., 2500.));
  const Acts::Vector3 position =
      SHiP::ActsFrame::positionToActs(line.x(wire.z), line.y(wire.z), wire.z);
  const Acts::Vector3 direction =
      (SHiP::ActsFrame::toActsRotation() * Acts::Vector3(line.tx, line.ty, 1.))
          .normalized();
  const auto pca = surface->intersect(gctx, position, direction).closest();
  const auto local = surface->globalToLocal(gctx, pca.position(), direction);
  return local.value()[0] / SHiP::ActsFrame::kShipLength;
}

void testSignConvention() {
  for (const int view : {0, 1, 2}) {
    for (const double offset : {-0.4, 0.7}) {
      const auto wire = makeWire(1, view, 0, viewAngle(view), 0., 100.);
      SHiP::LineSegment line;
      line.z0 = 100.;
      // Move the track off the wire along its normal
      line.x0 =
          -std::sin(viewAngle(view)) * offset + 0.3 * std::cos(viewAngle(view));
      line.y0 =
          std::cos(viewAngle(view)) * offset + 0.3 * std::sin(viewAngle(view));
      line.tx = 0.02;
      line.ty = -0.03;
      const double ours = SHiP::signedWireDistance(line, wire);
      const double acts = actsLoc0(line, wire);
      check(std::abs(ours - acts) < 1e-6,
            "signed wire distance matches ACTS straw loc0");
      check(std::abs(std::abs(ours) - std::abs(offset)) < 0.01,
            "signed wire distance has the expected size");
    }
  }
}

/// Hits of a straight line in the four views and two layers of a station
void addStation(int station, double z0, const SHiP::LineSegment& line,
                std::vector<SHiP::StrawWire>& wires) {
  for (int view = 0; view < 4; ++view) {
    for (int layer = 0; layer < 2; ++layer) {
      const double z = z0 + 10. * view + 2. * layer;
      const double angle = viewAngle(view);
      // Coordinate of the track along the normal to the wires
      const double u =
          -std::sin(angle) * line.x(z) + std::cos(angle) * line.y(z);
      const double stagger = layer * kPitch / 2.;
      const double offset =
          std::round((u - stagger) / kPitch) * kPitch + stagger;
      wires.push_back(makeWire(station, view, layer, angle, offset, z));
    }
  }
}

void testFindsSyntheticTrack() {
  // A track bent in y at the magnet, at z = 500 cm, by a field integral of
  // 0.65 T m: positive charge, 10 GeV
  constexpr double bendingZ = 500.;
  constexpr double fieldIntegral = 0.65;
  constexpr double momentum = 10.;
  SHiP::LineSegment up;
  up.z0 = bendingZ;
  up.x0 = 12.;
  up.tx = 0.01;
  up.y0 = -20.;
  up.ty = 0.005;
  SHiP::LineSegment down = up;
  down.ty = up.ty + 0.299792458 * fieldIntegral / momentum;

  std::vector<SHiP::StrawWire> wires;
  addStation(1, 0., up, wires);
  addStation(2, 200., up, wires);
  addStation(3, 800., down, wires);
  addStation(4, 1000., down, wires);
  std::vector<SHiP::PatRecHit> hits;
  for (std::size_t i = 0; i < wires.size(); ++i) {
    const auto& line = wires[i].station <= 2 ? up : down;
    hits.push_back({static_cast<int>(i), &wires[i],
                    std::abs(SHiP::signedWireDistance(line, wires[i])), 0.012});
  }

  const SHiP::StrawPatRec patRec(SHiP::StrawPatRec::Config{}, bendingZ,
                                 fieldIntegral);
  // Every matching pair of segments is a candidate, best match first; the
  // best is the track
  const auto tracks = patRec.findTracks(hits);
  check(!tracks.empty(), "track found");
  if (tracks.empty()) {
    return;
  }
  const auto& track = tracks.front();
  check(track.charge == 1, "charge from the kink");
  check(std::abs(track.momentum - momentum) / momentum < 0.01,
        "momentum from the kink");
  check(track.upstream.hits.size() == 16 && track.downstream.hits.size() == 16,
        "all hits on the segments");
  for (const auto* segment : {&track.upstream, &track.downstream}) {
    const auto& truth = segment == &track.upstream ? up : down;
    check(std::abs(segment->x(bendingZ) - truth.x(bendingZ)) < 0.01 &&
              std::abs(segment->y(bendingZ) - truth.y(bendingZ)) < 0.01,
          "segment position");
    for (std::size_t k = 0; k < segment->hits.size(); ++k) {
      const auto& wire = wires[segment->hits[k]];
      const double distance = SHiP::signedWireDistance(truth, wire);
      check(std::abs(distance) < 0.05 ||
                segment->signs[k] == (distance >= 0. ? 1 : -1),
            "side of the wire");
    }
  }
}

}  // namespace

int main() {
  testSignConvention();
  testFindsSyntheticTrack();
  if (failures == 0) {
    std::cout << "All straw pattern recognition tests passed" << std::endl;
  }
  return failures == 0 ? 0 : 1;
}
