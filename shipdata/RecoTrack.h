// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPDATA_RECOTRACK_H_
#define SHIPDATA_RECOTRACK_H_

#include <array>
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

  ClassDefOverride(RecoTrack, 2);
};

}  // namespace SHiP

#endif  // SHIPDATA_RECOTRACK_H_
