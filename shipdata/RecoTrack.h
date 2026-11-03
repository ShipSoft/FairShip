// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPDATA_RECOTRACK_H_
#define SHIPDATA_RECOTRACK_H_

#include <array>
#include <limits>
#include <vector>

#include "Rtypes.h"
#include "TObject.h"
#include "TVector3.h"

namespace SHiP {

/// Fitted track from the ACTS straw tracker fit, in the SHiP frame.
///
/// The state is taken at the first measurement of the track. Positions are
/// in cm, momenta in GeV. The covariance is the 6x6 matrix of (x, y, z, px,
/// py, pz), stored as its upper triangle in row-major order, so the variances
/// of px, py and pz are elements 15, 18 and 20.
///
/// The class does not depend on ACTS, so reco files can be read without it.
class RecoTrack : public TObject {
 public:
  RecoTrack() = default;
  RecoTrack(const TVector3& position, const TVector3& momentum, Int_t charge,
            const std::array<Double_t, 21>& covariance, Double_t chi2,
            Double_t nDoF, UInt_t nMeasurements, std::vector<Double_t> x_fits,
            std::vector<Double_t> y_fits, std::vector<Double_t> z_fits,
            std::vector<Double_t> residuals, std::vector<Double_t> pulls);
  ~RecoTrack() override = default;

  Double_t x() const { return m_x; }
  Double_t y() const { return m_y; }
  Double_t z() const { return m_z; }
  Double_t px() const { return m_px; }
  Double_t py() const { return m_py; }
  Double_t pz() const { return m_pz; }
  Int_t charge() const { return m_charge; }
  Double_t err_x() const { return m_err_x; }
  Double_t err_y() const { return m_err_y; }
  Double_t err_z() const { return m_err_z; }
  Double_t err_px() const { return m_err_px; }
  Double_t err_py() const { return m_err_py; }
  Double_t err_pz() const { return m_err_pz; }
  Double_t chi2() const { return m_chi2; }
  Double_t nDoF() const { return m_nDoF; }
  UInt_t nMeasurements() const { return m_nMeasurements; }
  const std::vector<Double_t>& GetXFittedPoints() const { return m_x_fits; }
  const std::vector<Double_t>& GetYFittedPoints() const { return m_y_fits; }
  const std::vector<Double_t>& GetZFittedPoints() const { return m_z_fits; }
  /// Residuals of the smoothed states, in cm, ordered along the track.
  const std::vector<Double_t>& GetResiduals() const { return m_residuals; }
  const std::vector<Double_t>& GetPulls() const { return m_pulls; }
  const std::vector<Double_t>& GetCovarianceElements() const {
    return m_cov_elements;
  }

  /// Extrapolate the track along a straight line to the plane at `z` (cm).
  ///
  /// The fitted state is taken at the first measurement, so this is only
  /// accurate where the field between that point and `z` can be neglected.
  /// Returns false if the track is parallel to the plane.
  Bool_t ExtrapolateToZ(Double_t z, TVector3& position) const;

  /// Store the track propagated through the field from its first fitted
  /// measurement to the UBT, or from its last one to the timing detector,
  /// as given by ActsStrawTracker::ExtrapolateToZ: position (cm), momentum
  /// (GeV), the 6x6 (x, y, z, px, py, pz) covariance as its upper triangle
  /// in row-major order (21 elements; NaN if not 21) and the signed path
  /// length (cm) from that measurement to the plane.
  void SetUBTExtrapolation(const TVector3& position, const TVector3& momentum,
                           const std::vector<Double_t>& covariance,
                           Double_t pathLength);
  void SetTDExtrapolation(const TVector3& position, const TVector3& momentum,
                          const std::vector<Double_t>& covariance,
                          Double_t pathLength);
  /// Path length (cm) through the field from the first to the last fitted
  /// measurement (ActsStrawTracker::TrackLength)
  void SetTrackLength(Double_t length) { m_track_length = length; }

  /// Whether the extrapolations were stored (they are NaN otherwise)
  Bool_t HasUBTExtrapolation() const { return m_ubt_valid; }
  Bool_t HasTDExtrapolation() const { return m_td_valid; }
  TVector3 GetUBTPosition() const {
    return TVector3(m_ubt_x, m_ubt_y, m_ubt_z);
  }
  TVector3 GetUBTMomentum() const {
    return TVector3(m_ubt_px, m_ubt_py, m_ubt_pz);
  }
  TVector3 GetTDPosition() const { return TVector3(m_td_x, m_td_y, m_td_z); }
  TVector3 GetTDMomentum() const { return TVector3(m_td_px, m_td_py, m_td_pz); }
  /// Upper triangle of the 6x6 covariance at the plane (empty if not
  /// stored); the variances of x, y, px, py and pz are elements 0, 6, 15,
  /// 18 and 20
  const std::vector<Double_t>& GetUBTCovariance() const { return m_ubt_cov; }
  const std::vector<Double_t>& GetTDCovariance() const { return m_td_cov; }
  /// Signed path length (cm): from the first measurement back to the UBT
  /// (negative), and from the last measurement on to the timing detector
  Double_t GetUBTPathLength() const { return m_ubt_path_len; }
  Double_t GetTDPathLength() const { return m_td_path_len; }
  /// Path length (cm) from the first to the last fitted measurement, NaN if
  /// not stored. The UBT to timing detector path is then
  /// GetTDPathLength() + GetTrackLength() - GetUBTPathLength().
  Double_t GetTrackLength() const { return m_track_length; }

 private:
  Double_t m_x{0.};
  Double_t m_y{0.};
  Double_t m_z{0.};
  Double_t m_px{0.};
  Double_t m_py{0.};
  Double_t m_pz{0.};
  Int_t m_charge{0};
  Double_t m_err_x{0.};
  Double_t m_err_y{0.};
  Double_t m_err_z{0.};
  Double_t m_err_px{0.};
  Double_t m_err_py{0.};
  Double_t m_err_pz{0.};
  Double_t m_chi2{0.};
  Double_t m_nDoF{0.};
  UInt_t m_nMeasurements{0};
  std::vector<Double_t> m_residuals;
  std::vector<Double_t> m_x_fits;
  std::vector<Double_t> m_y_fits;
  std::vector<Double_t> m_z_fits;
  std::vector<Double_t> m_pulls;
  std::vector<Double_t> m_cov_elements;
  // Propagated through the field (ACTS): UBT from the first measurement,
  // timing detector from the last; NaN if not stored
  Bool_t m_ubt_valid{false};
  Double_t m_ubt_x{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_ubt_y{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_ubt_z{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_ubt_px{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_ubt_py{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_ubt_pz{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_ubt_path_len{std::numeric_limits<Double_t>::quiet_NaN()};
  std::vector<Double_t> m_ubt_cov;
  Bool_t m_td_valid{false};
  Double_t m_td_x{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_td_y{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_td_z{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_td_px{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_td_py{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_td_pz{std::numeric_limits<Double_t>::quiet_NaN()};
  Double_t m_td_path_len{std::numeric_limits<Double_t>::quiet_NaN()};
  std::vector<Double_t> m_td_cov;
  /// Path length from the first to the last measurement (cm)
  Double_t m_track_length{std::numeric_limits<Double_t>::quiet_NaN()};

  ClassDefOverride(RecoTrack, 2);
};

}  // namespace SHiP

#endif  // SHIPDATA_RECOTRACK_H_
