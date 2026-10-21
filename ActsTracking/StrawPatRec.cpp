// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "StrawPatRec.hpp"

#include <Eigen/Dense>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <tuple>
#include <unordered_map>
#include <utility>

namespace SHiP {

namespace {

/// GeV per (T m) for a unit charge
constexpr double kKick = 0.299792458;

/// Highest momentum the magnet kink is taken to measure (GeV)
constexpr double kMaxMomentum = 1000.;

/// x lines kept per y line. Where tracks overlap in y, the stereo hits of a
/// neighbour also give a line, so the best one need not be this track's;
/// the fit of the whole track decides.
constexpr int kXLinesPerYLine = 4;
/// x lines of one y line sharing more than this fraction of hits are the
/// same line
constexpr double kSameLineFraction = 0.75;

/// Margin of the bisection window of `closestHit` (cm), for wires parallel
/// and in a z plane only to rounding
constexpr double kWindowMargin = 1e-4;

/// Unit vector along d x t for a wire d and the track direction t, which
/// gives the sign of the ACTS straw surface loc0
Eigen::Vector3d signDirection(const LineSegment& line, const StrawWire& wire) {
  const Eigen::Vector3d t = Eigen::Vector3d(line.tx, line.ty, 1.).normalized();
  const Eigen::Vector3d d(wire.dx, wire.dy, wire.dz);
  return d.cross(t).normalized();
}

/// `signDirection` and `signedWireDistance` for the wires of one line. The
/// direction depends only on the slopes of the line and of the wire, and the
/// wires of a view share their direction, so it is computed once per wire
/// direction (with the same arithmetic, so the results are identical). The
/// line must not change while this is in use.
class SignDirections {
 public:
  explicit SignDirections(const LineSegment& line)
      : m_line(line), m_t(Eigen::Vector3d(line.tx, line.ty, 1.).normalized()) {}

  Eigen::Vector3d operator()(const StrawWire& wire) {
    const double d[3] = {wire.dx, wire.dy, wire.dz};
    for (const auto& entry : m_cache) {
      if (std::memcmp(entry.d, d, sizeof d) == 0) {
        return entry.m;
      }
    }
    const Eigen::Vector3d m =
        Eigen::Vector3d(wire.dx, wire.dy, wire.dz).cross(m_t).normalized();
    m_cache.push_back({{wire.dx, wire.dy, wire.dz}, m});
    return m;
  }

  double distance(const StrawWire& wire) {
    const Eigen::Vector3d p(m_line.x(wire.z), m_line.y(wire.z), wire.z);
    const Eigen::Vector3d c(wire.x, wire.y, wire.z);
    return (p - c).dot((*this)(wire));
  }

 private:
  struct Entry {
    double d[3];
    Eigen::Vector3d m;
  };
  const LineSegment& m_line;
  Eigen::Vector3d m_t;
  std::vector<Entry> m_cache;
};

bool isStereo(const StrawWire& wire) {
  return wire.view == 1 || wire.view == 2;
}

bool isUpstream(const StrawWire& wire) { return wire.station <= 2; }

/// Layers of one kind of view in one pair of stations, ordered in z
using Layers = std::vector<std::vector<int>>;

Layers groupLayers(const std::vector<PatRecHit>& hits,
                   const std::vector<int>& selected) {
  std::map<std::tuple<int, int, int>, std::vector<int>> byLayer;
  for (const int i : selected) {
    const auto& w = *hits[i].wire;
    byLayer[{w.station, w.view, w.layer}].push_back(i);
  }
  Layers layers;
  for (auto& [key, members] : byLayer) {
    layers.push_back(std::move(members));
  }
  std::sort(layers.begin(), layers.end(),
            [&hits](const auto& a, const auto& b) {
              return hits[a.front()].wire->z < hits[b.front()].wire->z;
            });
  return layers;
}

/// Ranking of segments: more hits first, then the better fit
bool better(const LineSegment& a, const LineSegment& b) {
  if (a.hits.size() != b.hits.size()) {
    return a.hits.size() > b.hits.size();
  }
  return a.chi2 < b.chi2;
}

/// Keep the best of each set of conflicting segments: those sharing more
/// than `maxShared` hits, or more than `maxFraction` of the hits of the
/// shorter one
std::vector<LineSegment> removeDuplicates(std::vector<LineSegment> segments,
                                          int maxShared,
                                          double maxFraction = 1.) {
  std::sort(segments.begin(), segments.end(), better);
  std::vector<LineSegment> kept;
  // Kept segments by hit: only segments sharing a hit can conflict, and a
  // segment has at most one hit per layer, so the shared hits are counted
  // from the kept segments of each of its hits
  std::unordered_map<int, std::vector<std::size_t>> keptOfHit;
  std::vector<int> shared;
  std::vector<std::size_t> sharing;
  for (auto& segment : segments) {
    sharing.clear();
    for (const int h : segment.hits) {
      const auto it = keptOfHit.find(h);
      if (it == keptOfHit.end()) {
        continue;
      }
      for (const std::size_t k : it->second) {
        if (shared[k]++ == 0) {
          sharing.push_back(k);
        }
      }
    }
    const bool duplicate =
        std::any_of(sharing.begin(), sharing.end(), [&](std::size_t k) {
          const auto shorter =
              std::min(segment.hits.size(), kept[k].hits.size());
          return shared[k] > maxShared || shared[k] > maxFraction * shorter;
        });
    for (const std::size_t k : sharing) {
      shared[k] = 0;
    }
    if (!duplicate) {
      for (const int h : segment.hits) {
        keptOfHit[h].push_back(kept.size());
      }
      kept.push_back(std::move(segment));
      shared.push_back(0);
    }
  }
  return kept;
}

/// Keep one line of each set of lines with the same hits on the same sides,
/// the one with the best fit, in the order the lines were found
std::vector<LineSegment> uniqueLines(std::vector<LineSegment> lines) {
  std::map<std::vector<std::pair<int, int>>, std::size_t> best;
  std::vector<bool> keep(lines.size(), false);
  for (std::size_t i = 0; i < lines.size(); ++i) {
    std::vector<std::pair<int, int>> key;
    key.reserve(lines[i].hits.size());
    for (std::size_t k = 0; k < lines[i].hits.size(); ++k) {
      key.emplace_back(lines[i].hits[k], lines[i].signs[k]);
    }
    std::sort(key.begin(), key.end());
    const auto [it, inserted] = best.emplace(std::move(key), i);
    if (inserted) {
      keep[i] = true;
    } else if (lines[i].chi2 < lines[it->second].chi2) {
      keep[it->second] = false;
      keep[i] = true;
      it->second = i;
    }
  }
  std::vector<LineSegment> unique;
  for (std::size_t i = 0; i < lines.size(); ++i) {
    if (keep[i]) {
      unique.push_back(std::move(lines[i]));
    }
  }
  return unique;
}

/// Least-squares fit of a straight line to signed drift distances.
///
/// The side of each wire is taken from the current line and re-evaluated
/// after each fit until it no longer changes. With `fitX` false, only y0
/// and ty are fitted (y views alone do not constrain x). Hits further than
/// `outlierCut` from the line are dropped.
bool fitLine(LineSegment& line, const std::vector<PatRecHit>& hits, bool fitX,
             double outlierCut) {
  for (int iteration = 0; iteration < 10; ++iteration) {
    const int n = static_cast<int>(line.hits.size());
    const int nPar = fitX ? 4 : 2;
    if (n < nPar + 1) {
      return false;
    }
    double zSum = 0.;
    for (const int h : line.hits) {
      zSum += hits[h].wire->z;
    }
    const double z0 = zSum / n;
    // Re-express the current line around the new reference z
    line.x0 = line.x(z0);
    line.y0 = line.y(z0);
    line.z0 = z0;

    // Signs from the current line
    SignDirections sign(line);
    std::vector<int> signs(n);
    bool changed = line.signs.size() != static_cast<std::size_t>(n);
    for (int k = 0; k < n; ++k) {
      const double predicted = sign.distance(*hits[line.hits[k]].wire);
      signs[k] = predicted >= 0. ? 1 : -1;
      changed = changed || signs[k] != line.signs[k];
    }
    line.signs = signs;

    // Normal equations of the weighted least squares, at most 4x4
    Eigen::Matrix4d ata = Eigen::Matrix4d::Zero();
    Eigen::Vector4d atb = Eigen::Vector4d::Zero();
    for (int k = 0; k < n; ++k) {
      const auto& hit = hits[line.hits[k]];
      const auto& w = *hit.wire;
      const Eigen::Vector3d m = sign(w);
      const double dz = w.z - z0;
      const double weight = 1. / (hit.sigma * hit.sigma);
      // m . (P - c), with P = (x0 + tx dz, y0 + ty dz, w.z)
      double rhs = signs[k] * hit.drift + m.x() * w.x + m.y() * w.y;
      Eigen::Vector4d row;
      if (fitX) {
        row << m.x(), m.x() * dz, m.y(), m.y() * dz;
      } else {
        row << m.y(), m.y() * dz, 0., 0.;
        rhs -= m.x() * line.x(w.z);
      }
      ata.noalias() += weight * row * row.transpose();
      atb += weight * rhs * row;
    }
    Eigen::Vector4d p = Eigen::Vector4d::Zero();
    if (fitX) {
      p = ata.ldlt().solve(atb);
    } else {
      p.head<2>() = ata.topLeftCorner<2, 2>().ldlt().solve(atb.head<2>());
    }
    if (!p.allFinite()) {
      return false;
    }
    if (fitX) {
      line.x0 = p(0);
      line.tx = p(1);
      line.y0 = p(2);
      line.ty = p(3);
    } else {
      line.y0 = p(0);
      line.ty = p(1);
    }

    // Residuals, and the worst outlier
    SignDirections fitted(line);
    line.chi2 = 0.;
    int worst = -1;
    double worstResidual = outlierCut;
    for (int k = 0; k < n; ++k) {
      const auto& hit = hits[line.hits[k]];
      const double residual = signs[k] * hit.drift - fitted.distance(*hit.wire);
      line.chi2 += residual * residual / (hit.sigma * hit.sigma);
      if (std::abs(residual) > worstResidual) {
        worstResidual = std::abs(residual);
        worst = k;
      }
    }
    if (worst >= 0) {
      line.hits.erase(line.hits.begin() + worst);
      line.signs.erase(line.signs.begin() + worst);
      continue;
    }
    if (!changed) {
      return true;
    }
  }
  return true;
}

/// The hits of one layer sorted by the position of their wire across the
/// wires, so that `closestHit` bisects instead of scanning the layer
struct LayerIndex {
  /// False if the wires are not parallel in a plane of constant z: the
  /// layer is then scanned
  bool sorted{false};
  /// Unit vector across the wires, d x z
  double mx{0.};
  double my{0.};
  /// z of the first wire, and the largest offset of the others from it
  double z{0.};
  double dzMax{0.};
  double maxDrift{0.};
  /// (position along (mx, my), position in the layer)
  std::vector<std::pair<double, int>> byPosition;
};

LayerIndex indexLayer(const std::vector<int>& layer,
                      const std::vector<PatRecHit>& hits) {
  LayerIndex index;
  const auto& first = *hits[layer.front()].wire;
  for (const int h : layer) {
    const auto& w = *hits[h].wire;
    if (std::abs(w.dz) > 1e-9 ||
        std::abs(w.dx * first.dy - w.dy * first.dx) > 1e-9) {
      return index;
    }
  }
  const double norm = std::hypot(first.dx, first.dy);
  index.mx = first.dy / norm;
  index.my = -first.dx / norm;
  index.z = first.z;
  for (int k = 0; k < static_cast<int>(layer.size()); ++k) {
    const auto& hit = hits[layer[k]];
    const auto& w = *hit.wire;
    index.dzMax = std::max(index.dzMax, std::abs(w.z - index.z));
    index.maxDrift = std::max(index.maxDrift, hit.drift);
    index.byPosition.emplace_back(w.x * index.mx + w.y * index.my, k);
  }
  std::sort(index.byPosition.begin(), index.byPosition.end());
  index.sorted = true;
  return index;
}

std::vector<LayerIndex> indexLayers(const std::vector<std::vector<int>>& layers,
                                    const std::vector<PatRecHit>& hits) {
  std::vector<LayerIndex> indices;
  indices.reserve(layers.size());
  for (const auto& layer : layers) {
    indices.push_back(indexLayer(layer, hits));
  }
  return indices;
}

/// Hit in `layer` closest to the line within `tolerance`, or -1; of equally
/// close hits the first in the layer.
///
/// A hit within `tolerance` is less than maxDrift + tolerance from the line.
/// For a wire d in a plane of constant z, that distance is b (m . u), with b
/// the offset across the wires in that plane, m = d x z and u the unit
/// vector along d x t. As m . u = t_z / |d x t| >= t_z, such a hit has
/// |b| < (maxDrift + tolerance) / t_z, so only the wires within that (plus
/// the slope over the z spread of the layer) of the line are tried.
int closestHit(const LineSegment& line, const std::vector<int>& layer,
               const LayerIndex& index, const std::vector<PatRecHit>& hits,
               double tolerance, SignDirections& sign) {
  int best = -1;
  int bestPosition = 0;
  double bestDistance = tolerance;
  const auto consider = [&](int position) {
    const int h = layer[position];
    const double distance =
        std::abs(std::abs(sign.distance(*hits[h].wire)) - hits[h].drift);
    if (distance < bestDistance ||
        (best >= 0 && distance == bestDistance && position < bestPosition)) {
      bestDistance = distance;
      best = h;
      bestPosition = position;
    }
  };
  if (!index.sorted) {
    for (int k = 0; k < static_cast<int>(layer.size()); ++k) {
      consider(k);
    }
    return best;
  }
  const double halfWidth =
      (index.maxDrift + tolerance) *
          std::sqrt(1. + line.tx * line.tx + line.ty * line.ty) +
      index.dzMax * std::hypot(line.tx, line.ty) + kWindowMargin;
  const double centre = line.x(index.z) * index.mx + line.y(index.z) * index.my;
  auto it = std::lower_bound(
      index.byPosition.begin(), index.byPosition.end(), centre - halfWidth,
      [](const auto& entry, double value) { return entry.first < value; });
  for (; it != index.byPosition.end() && it->first <= centre + halfWidth;
       ++it) {
    consider(it->second);
  }
  return best;
}

int countHits(const LineSegment& line, const std::vector<PatRecHit>& hits,
              bool (*select)(const StrawWire&)) {
  return std::count_if(line.hits.begin(), line.hits.end(),
                       [&](int h) { return select(*hits[h].wire); });
}

bool isY(const StrawWire& wire) { return !isStereo(wire); }

/// Pairs of layers to seed lines from: one of the first two with one of the
/// last two layers, over all layers and within each station, so that tracks
/// crossing only one station of the pair are seeded too
std::vector<std::pair<int, int>> seedLayerPairs(
    const Layers& layers, const std::vector<PatRecHit>& hits) {
  std::set<std::pair<int, int>> pairs;
  const auto addPairs = [&](int first, int last) {
    const int n = last - first;
    if (n < 2) {
      return;
    }
    const int edge = std::min(2, n / 2);
    for (int la = first; la < first + edge; ++la) {
      for (int lb = last - edge; lb < last; ++lb) {
        pairs.emplace(la, lb);
      }
    }
  };
  const int nLayers = static_cast<int>(layers.size());
  addPairs(0, nLayers);
  int first = 0;
  for (int l = 1; l <= nLayers; ++l) {
    if (l == nLayers || hits[layers[l].front()].wire->station !=
                            hits[layers[first].front()].wire->station) {
      addPairs(first, l);
      first = l;
    }
  }
  return {pairs.begin(), pairs.end()};
}
bool isU(const StrawWire& wire) { return wire.view == 1; }
bool isV(const StrawWire& wire) { return wire.view == 2; }

}  // namespace

double signedWireDistance(const LineSegment& line, const StrawWire& wire) {
  const Eigen::Vector3d p(line.x(wire.z), line.y(wire.z), wire.z);
  const Eigen::Vector3d c(wire.x, wire.y, wire.z);
  return (p - c).dot(signDirection(line, wire));
}

StrawPatRec::StrawPatRec(const Config& config, double bendingZ,
                         double fieldIntegral)
    : m_cfg(config), m_bendingZ(bendingZ), m_fieldIntegral(fieldIntegral) {}

std::vector<LineSegment> StrawPatRec::findSegments(
    const std::vector<PatRecHit>& hits, bool upstream, int maxSegments) const {
  std::vector<int> yHits;
  std::vector<int> stereoHits;
  for (int i = 0; i < static_cast<int>(hits.size()); ++i) {
    const auto& w = *hits[i].wire;
    if (isUpstream(w) != upstream) {
      continue;
    }
    (isStereo(w) ? stereoHits : yHits).push_back(i);
  }
  const Layers yLayers = groupLayers(hits, yHits);
  const Layers stereoLayers = groupLayers(hits, stereoHits);
  const auto yIndex = indexLayers(yLayers, hits);
  const auto stereoIndex = indexLayers(stereoLayers, hits);
  const int nY = static_cast<int>(yLayers.size());
  const int nStereo = static_cast<int>(stereoLayers.size());
  if (nY < m_cfg.minYHits || nStereo < m_cfg.minStereoHits) {
    return {};
  }
  // Seeds pair a hit in one of the first two layers with one in the last two,
  // of the pair of stations and of each station

  // y lines from pairs of drift circles: the two candidate y positions of
  // each hit give four lines per pair
  std::vector<LineSegment> yLines;
  for (const auto& [la, lb] : seedLayerPairs(yLayers, hits)) {
    {
      for (const int a : yLayers[la]) {
        for (const int b : yLayers[lb]) {
          const auto& wa = *hits[a].wire;
          const auto& wb = *hits[b].wire;
          for (const int sa : {-1, 1}) {
            for (const int sb : {-1, 1}) {
              LineSegment line;
              line.z0 = wa.z;
              line.y0 = wa.y + sa * hits[a].drift;
              line.ty = (wb.y + sb * hits[b].drift - line.y0) / (wb.z - wa.z);
              if (std::abs(line.ty) > m_cfg.maxSlope) {
                continue;
              }
              line.hits = {a, b};
              SignDirections sign(line);
              for (int l = 0; l < nY; ++l) {
                if (l == la || l == lb) {
                  continue;
                }
                const int h = closestHit(line, yLayers[l], yIndex[l], hits,
                                         m_cfg.tolerance, sign);
                if (h >= 0) {
                  line.hits.push_back(h);
                }
              }
              if (static_cast<int>(line.hits.size()) < m_cfg.minYHits) {
                continue;
              }
              if (fitLine(line, hits, false, m_cfg.tolerance) &&
                  static_cast<int>(line.hits.size()) >= m_cfg.minYHits) {
                yLines.push_back(std::move(line));
              }
            }
          }
        }
      }
    }
  }
  // A track crossing all layers is seeded by every pair of seed layers, and
  // the seeds converge to the same line: one line per set of hits and sides
  // is kept. Lines sharing only some hits are kept: tracks that overlap in y
  // have similar y lines, and are told apart only in the stereo views, and
  // the same hits can fit with the sides of some wires mirrored, which
  // projects the stereo hits differently. Duplicate segments are removed
  // after the stereo views.
  yLines = uniqueLines(std::move(yLines));
  // The search in the stereo views grows with the number of y lines; in
  // showers, with thousands of hits, only the best are searched
  if (m_cfg.maxYLines > 0 &&
      static_cast<int>(yLines.size()) > m_cfg.maxYLines) {
    std::stable_sort(yLines.begin(), yLines.end(), better);
    yLines.resize(m_cfg.maxYLines);
  }

  // For each y line, find the x line in the stereo views. Each stereo hit
  // gives two x positions, one for each side of the wire.
  struct XPoint {
    int hit;
    double z;
    double x;
  };
  std::vector<LineSegment> segments;
  for (const auto& yLine : yLines) {
    std::vector<std::vector<XPoint>> points(nStereo);
    SignDirections ySign(yLine);
    for (int l = 0; l < nStereo; ++l) {
      for (const int h : stereoLayers[l]) {
        const auto& w = *hits[h].wire;
        const Eigen::Vector3d m = ySign(w);
        if (std::abs(m.x()) < 1e-3) {
          continue;
        }
        for (const int s : {-1, 1}) {
          const double x =
              w.x + (s * hits[h].drift - m.y() * (yLine.y(w.z) - w.y)) / m.x();
          // Only where the wire actually is
          const double along = (x - w.x) * w.dx + (yLine.y(w.z) - w.y) * w.dy;
          if (std::abs(along) <= w.halfLength) {
            points[l].push_back({h, w.z, x});
          }
        }
      }
    }
    // Several x lines per y line (see kXLinesPerYLine)
    std::vector<LineSegment> xLines;
    for (const auto& [la, lb] : seedLayerPairs(stereoLayers, hits)) {
      {
        for (const auto& pa : points[la]) {
          for (const auto& pb : points[lb]) {
            LineSegment line = yLine;
            line.tx = (pb.x - pa.x) / (pb.z - pa.z);
            if (std::abs(line.tx) > m_cfg.maxSlopeX) {
              continue;
            }
            line.x0 = pa.x + line.tx * (line.z0 - pa.z);
            line.signs.clear();
            line.hits.push_back(pa.hit);
            line.hits.push_back(pb.hit);
            SignDirections sign(line);
            for (int l = 0; l < nStereo; ++l) {
              if (l == la || l == lb) {
                continue;
              }
              const int h = closestHit(line, stereoLayers[l], stereoIndex[l],
                                       hits, m_cfg.tolerance, sign);
              if (h >= 0) {
                line.hits.push_back(h);
              }
            }
            // The fit only drops hits, so lines short of hits before the fit
            // fail after it
            if (countHits(line, hits, isStereo) < m_cfg.minStereoHits ||
                countHits(line, hits, isU) < m_cfg.minHitsPerStereoView ||
                countHits(line, hits, isV) < m_cfg.minHitsPerStereoView) {
              continue;
            }
            if (fitLine(line, hits, true, m_cfg.tolerance) &&
                countHits(line, hits, isY) >= m_cfg.minYHits &&
                countHits(line, hits, isStereo) >= m_cfg.minStereoHits &&
                countHits(line, hits, isU) >= m_cfg.minHitsPerStereoView &&
                countHits(line, hits, isV) >= m_cfg.minHitsPerStereoView) {
              xLines.push_back(std::move(line));
            }
          }
        }
      }
    }
    xLines = removeDuplicates(
        std::move(xLines), std::numeric_limits<int>::max(), kSameLineFraction);
    if (static_cast<int>(xLines.size()) > kXLinesPerYLine) {
      xLines.resize(kXLinesPerYLine);
    }
    for (auto& line : xLines) {
      segments.push_back(std::move(line));
    }
  }
  // Only near-duplicates are removed here. Neighbouring tracks share
  // straws, and the choice between conflicting candidates is left to the
  // fit of the whole track.
  segments = removeDuplicates(std::move(segments), m_cfg.maxSharedHits);
  if (maxSegments > 0 && static_cast<int>(segments.size()) > maxSegments) {
    segments.resize(maxSegments);
  }
  return segments;
}

std::optional<TrackCandidate> StrawPatRec::match(
    const LineSegment& upstream, const LineSegment& downstream) const {
  TrackCandidate candidate{upstream, downstream};
  // The field kicks the track in y by q * kKick * integral(Bx dz) / pz
  const double kink = downstream.ty - upstream.ty;
  const double kick = kKick * m_fieldIntegral;
  if (kink == 0. || kick == 0.) {
    return std::nullopt;
  }
  const double pz = std::min(std::abs(kick / kink), kMaxMomentum);
  candidate.momentum = pz * std::sqrt(1. + upstream.tx * upstream.tx +
                                      upstream.ty * upstream.ty);
  candidate.charge = kink / kick > 0. ? 1 : -1;

  const double z = m_bendingZ;
  const double p = candidate.momentum;
  const auto sigma = [p](double a, double b) { return std::hypot(a, b / p); };
  const double dx = (upstream.x(z) - downstream.x(z)) /
                    sigma(m_cfg.matchSigmaX, m_cfg.matchSigmaXPerP);
  const double dtx = (upstream.tx - downstream.tx) /
                     sigma(m_cfg.matchSigmaTx, m_cfg.matchSigmaTxPerP);
  const double dy = (upstream.y(z) - downstream.y(z)) /
                    sigma(m_cfg.matchSigmaY, m_cfg.matchSigmaYPerP);
  candidate.matchChi2 = dx * dx + dtx * dtx + dy * dy;
  return candidate;
}

std::vector<TrackCandidate> StrawPatRec::matchSegments(
    const std::vector<LineSegment>& upstream,
    const std::vector<LineSegment>& downstream) const {
  std::vector<TrackCandidate> pairs;
  for (const auto& u : upstream) {
    for (const auto& d : downstream) {
      auto candidate = match(u, d);
      if (candidate &&
          (candidate->matchChi2 < m_cfg.maxMatchChi2 ||
           (candidate->momentum < m_cfg.lowMomentum &&
            candidate->matchChi2 < m_cfg.maxLowMomentumMatchChi2))) {
        pairs.push_back(std::move(*candidate));
      }
    }
  }
  // Every pair is a candidate, best match first: the best match of a segment
  // is often not its track, and the fit of the whole track resolves the
  // candidates sharing a segment
  std::sort(pairs.begin(), pairs.end(), [](const auto& a, const auto& b) {
    return a.matchChi2 < b.matchChi2;
  });
  return pairs;
}

std::vector<TrackCandidate> StrawPatRec::findTracks(
    const std::vector<PatRecHit>& hits) const {
  return matchSegments(findSegments(hits, true, 0),
                       findSegments(hits, false, 0));
}

std::optional<TrackCandidate> StrawPatRec::fitCandidate(
    const std::vector<PatRecHit>& hits) const {
  const auto upstream = findSegments(hits, true, 1);
  const auto downstream = findSegments(hits, false, 1);
  if (upstream.empty() || downstream.empty()) {
    return std::nullopt;
  }
  return match(upstream.front(), downstream.front());
}

}  // namespace SHiP
