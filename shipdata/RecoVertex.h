// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPDATA_RECOVERTEX_H_
#define SHIPDATA_RECOVERTEX_H_

#include <array>
#include <vector>

#include "Rtypes.h"
#include "TObject.h"
#include "TVector3.h"

namespace SHiP {

/// Fitted vertex from the ACTS straw tracker vertex fit, in the SHiP frame.
///
/// Positions are in cm, momenta in GeV. Covariances are stored as the upper
/// triangle of the 3x3 matrix in row-major order: (0,0), (0,1), (0,2), (1,1),
/// (1,2), (2,2).
///
/// The class does not depend on ACTS, so reco files can be read without it.
class RecoVertex : public TObject {
 public:
  RecoVertex() = default;
  RecoVertex(const TVector3& position,
             const std::array<Double_t, 6>& covariance, Double_t chi2,
             Double_t nDoF);
  ~RecoVertex() override = default;

  /// Add a track fitted to this vertex.
  ///
  /// `trackId` is the index of the track in the RecoTracks branch,
  /// `momentum` its momentum at the vertex and `momentumCovariance` the
  /// covariance of that momentum.
  void AddTrack(Int_t trackId, const TVector3& momentum,
                const std::array<Double_t, 6>& momentumCovariance);
  /// Distance of closest approach of the two tracks, before the vertex fit
  void SetDoca(Double_t doca) { m_doca = doca; }

  Double_t x() const { return m_x; }
  Double_t y() const { return m_y; }
  Double_t z() const { return m_z; }
  Double_t err_x() const { return m_err_x; }
  Double_t err_y() const { return m_err_y; }
  Double_t err_z() const { return m_err_z; }
  Double_t chi2() const { return m_chi2; }
  Double_t nDoF() const { return m_nDoF; }
  /// Distance of closest approach in cm for two-track vertices, else -1
  Double_t doca() const { return m_doca; }
  const std::vector<Double_t>& GetCovarianceElements() const {
    return m_cov_elements;
  }

  const std::vector<Int_t>& trackIds() const { return m_trackIds; }
  const std::vector<Double_t>& trackPx() const { return m_trackPx; }
  const std::vector<Double_t>& trackPy() const { return m_trackPy; }
  const std::vector<Double_t>& trackPz() const { return m_trackPz; }
  /// Momentum covariance of track `i`, as 6 upper-triangle elements
  std::array<Double_t, 6> GetTrackMomentumCovariance(size_t i) const;

 private:
  Double_t m_x{0.};
  Double_t m_y{0.};
  Double_t m_z{0.};
  Double_t m_err_x{0.};
  Double_t m_err_y{0.};
  Double_t m_err_z{0.};
  Double_t m_chi2{0.};
  Double_t m_nDoF{0.};
  Double_t m_doca{-1.};
  std::vector<Double_t> m_cov_elements;
  std::vector<Int_t> m_trackIds;
  std::vector<Double_t> m_trackPx;
  std::vector<Double_t> m_trackPy;
  std::vector<Double_t> m_trackPz;
  /// Momentum covariances of all tracks, 6 elements per track
  std::vector<Double_t> m_trackCovP;

  ClassDefOverride(RecoVertex, 1);
};

}  // namespace SHiP

#endif  // SHIPDATA_RECOVERTEX_H_
