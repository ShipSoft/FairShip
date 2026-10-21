// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_STRAWPATREC_HPP_
#define ACTSTRACKING_STRAWPATREC_HPP_

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

  double x(double z) const { return x0 + tx * (z - z0); }
  double y(double z) const { return y0 + ty * (z - z0); }
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
    /// Uncertainties of the segment match at the bending plane, as
    /// sqrt(a^2 + (b / p)^2) with p in GeV: the straight segments extrapolated
    /// to the bending plane deviate more from the track the lower its
    /// momentum. From truth-matched segments of 2-100 GeV tracks, with the
    /// constant terms widened for busy events, where segments lose hits.
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
    /// Segments sharing more hits than this are the same segment
    int maxSharedHits = 12;
  };

  /// `bendingZ` is the centre of the field integral along z (cm) and
  /// `fieldIntegral` the integral of Bx along z through the magnet (T m).
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
                                      const LineSegment& downstream) const;

  Config m_cfg;
  double m_bendingZ;
  double m_fieldIntegral;
};

/// Signed distance of closest approach between a straight track and a wire,
/// with the sign convention of the ACTS straw surface (loc0)
double signedWireDistance(const LineSegment& line, const StrawWire& wire);

}  // namespace SHiP

#endif  // ACTSTRACKING_STRAWPATREC_HPP_
