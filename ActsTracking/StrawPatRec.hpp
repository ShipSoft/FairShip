// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_STRAWPATREC_HPP_
#define ACTSTRACKING_STRAWPATREC_HPP_

#include <functional>
#include <optional>
#include <vector>

#include "ActsStrawGeometry.hpp"

namespace SHiP {

/// A straw hit for pattern recognition: the wire and the unsigned drift
/// distance (cm).
struct PatRecHit {
  int index;
  const StrawWire* wire;
  double drift;
  double sigma;
};

/// A straight line x = x0 + tx (z - z0), y = y0 + ty (z - z0) in the SHiP
/// frame (cm), with the hits on it and the side of the wire each passed on.
struct LineSegment {
  double z0{0.};
  double x0{0.};
  double tx{0.};
  double y0{0.};
  double ty{0.};
  std::vector<int> hits;   ///< positions in the hit list
  std::vector<int> signs;  ///< signed drift distance = sign * drift
  double chi2{0.};
  /// Covariance of the fitted (x0, tx) and (y0, ty) at z0, from the hit
  /// uncertainties
  double varX0{0.}, covX0Tx{0.}, varTx{0.};
  double varY0{0.}, covY0Ty{0.}, varTy{0.};

  double x(double z) const { return x0 + tx * (z - z0); }
  double y(double z) const { return y0 + ty * (z - z0); }
  /// Variance of x(z) and y(z) from the fit
  double varX(double z) const {
    const double dz = z - z0;
    return varX0 + 2. * dz * covX0Tx + dz * dz * varTx;
  }
  double varY(double z) const {
    const double dz = z - z0;
    return varY0 + 2. * dz * covY0Ty + dz * dz * varTy;
  }
};

/// Field integrals along a straight line through the magnet
struct FieldIntegrals {
  double bx{0.};      ///< integral of Bx along z (T m)
  double by{0.};      ///< integral of By along z (T m)
  double centre{0.};  ///< z of the centre of the Bx integral (cm)
};

/// A track candidate: an upstream and a downstream segment matched across
/// the magnet, with the momentum estimated from the kink.
struct TrackCandidate {
  LineSegment upstream;
  LineSegment downstream;
  double momentum{0.};  ///< GeV
  int charge{0};
  double matchChi2{0.};
};

/// Straw tracker pattern recognition from drift circles.
///
/// The spectrometer has two stations before and two after the magnet, whose
/// field (mostly Bx) bends tracks in y. Within each pair of stations tracks
/// are straight lines, which are found from the drift circles of the hits:
/// first in the y views, then, for each y line, in the stereo views. The
/// segments before and after the magnet are then matched, which also gives
/// the momentum and charge.
class StrawPatRec {
 public:
  struct Config {
    /// Tolerance on the distance of a line from a drift circle (cm) when
    /// collecting hits
    double tolerance = 0.15;
    /// Minimum hits on a segment, of the 8 y and 8 stereo layers per pair
    /// of stations
    int minYHits = 4;
    int minStereoHits = 3;
    /// Minimum hits in each of the two stereo views. A y line with stereo hits
    /// of one view alone always gives a straight line, whichever track those
    /// hits are from; only the two views together fix x.
    int minHitsPerStereoView = 2;
    /// Largest track slopes considered. The magnet bends in y, so the slopes
    /// in x stay smaller: in neutrino DIS events, 0.1% of the reconstructible
    /// tracks have |tx| > 0.3 downstream of the magnet, 0.01% upstream.
    double maxSlope = 0.6;
    double maxSlopeX = 0.3;
    /// Most y lines searched for x lines per pair of stations, the best by
    /// hits and fit, or all if not positive
    int maxYLines = 4000;
    /// Uncertainties of the segment match at the bending plane, as
    /// sqrt(a^2 + (b / p)^2) with p in GeV: the straight segments extrapolated
    /// to the bending plane deviate more from the track the lower its
    /// momentum. From truth-matched segments of 2-100 GeV tracks, with the
    /// constant terms widened for busy events, where segments lose hits.
    /// The fit uncertainties of the two segments are added in quadrature, so
    /// a segment from a single station, e.g. of a track leaving the straws
    /// at large angle, is matched with its larger slope uncertainty.
    double matchSigmaX = 0.6;        ///< cm
    double matchSigmaXPerP = 3.;     ///< cm GeV
    double matchSigmaTx = 1.5e-3;    ///< rad
    double matchSigmaTxPerP = 0.02;  ///< rad GeV
    double matchSigmaY = 0.05;       ///< cm
    double matchSigmaYPerP = 0.5;    ///< cm GeV
    double maxMatchChi2 = 40.;
    /// Below this momentum (GeV) the straight segments describe the track
    /// through the magnet poorly, and pairs up to `maxLowMomentumMatchChi2`
    /// are kept for the track fit to decide
    double lowMomentum = 3.;
    double maxLowMomentumMatchChi2 = 400.;
    /// Lowest momentum of a match (GeV). A segment passing beside the field
    /// gives a small field integral, so a low momentum and wide uncertainties,
    /// and would match almost any segment.
    double minMomentum = 0.2;
    /// Segments sharing more hits than this are the same segment
    int maxSharedHits = 12;
  };

  /// The field integrals along a straight line through the magnet
  using FieldAlong = std::function<FieldIntegrals(const LineSegment&)>;

  /// Segments are matched with the field integrals along the pair: away from
  /// the axis the magnet also kicks tracks in x (By), and the centre of the
  /// kick in y moves. The track bends between the two straight lines, so the
  /// integrals along both are averaged.
  StrawPatRec(const Config& config, FieldAlong fieldAlong);
  /// The same field integrals for every segment: `bendingZ` is the centre
  /// of the Bx integral (cm) and `fieldIntegral` the integral (T m)
  StrawPatRec(const Config& config, double bendingZ, double fieldIntegral);

  /// Find tracks among all hits of the event
  std::vector<TrackCandidate> findTracks(
      const std::vector<PatRecHit>& hits) const;

  /// Fit the hits of one given candidate, resolving the left/right ambiguity.
  /// Returns nothing if the hits do not form segments on both sides.
  std::optional<TrackCandidate> fitCandidate(
      const std::vector<PatRecHit>& hits) const;

 private:
  std::vector<LineSegment> findSegments(const std::vector<PatRecHit>& hits,
                                        bool upstream, int maxSegments) const;
  std::vector<TrackCandidate> matchSegments(
      const std::vector<LineSegment>& upstream,
      const std::vector<LineSegment>& downstream) const;
  std::optional<TrackCandidate> match(const LineSegment& upstream,
                                      const LineSegment& downstream,
                                      const FieldIntegrals& field) const;
  static FieldIntegrals averageField(const FieldIntegrals& upstream,
                                     const FieldIntegrals& downstream);

  Config m_cfg;
  FieldAlong m_fieldAlong;
};

/// Signed distance of closest approach between a straight track and a wire,
/// with the sign convention of the ACTS straw surface (loc0)
double signedWireDistance(const LineSegment& line, const StrawWire& wire);

}  // namespace SHiP

#endif  // ACTSTRACKING_STRAWPATREC_HPP_
