// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "RecoTrack.h"

#include <algorithm>
#include <cmath>
#include <utility>

namespace SHiP {

RecoTrack::RecoTrack(const TVector3& position, const TVector3& momentum,
                     Int_t charge, const std::array<Double_t, 21>& covariance,
                     Double_t chi2, Double_t nDoF, UInt_t nMeasurements,
                     std::vector<Double_t> residuals,
                     std::vector<Double_t> pulls)
    : TObject(),
      m_x(position.X()),
      m_y(position.Y()),
      m_z(position.Z()),
      m_px(momentum.X()),
      m_py(momentum.Y()),
      m_pz(momentum.Z()),
      m_charge(charge),
      m_chi2(chi2),
      m_nDoF(nDoF),
      m_nMeasurements(nMeasurements),
      m_residuals(std::move(residuals)),
      m_pulls(std::move(pulls)),
      m_cov_elements(covariance.begin(), covariance.end()) {
  // Diagonal of the upper triangle of a 6x6 matrix, row-major
  auto sigma = [&covariance](int index) {
    return std::sqrt(std::max(0.0, covariance[index]));
  };
  m_err_x = sigma(0);
  m_err_y = sigma(6);
  m_err_z = sigma(11);
  m_err_px = sigma(15);
  m_err_py = sigma(18);
  m_err_pz = sigma(20);
}

Bool_t RecoTrack::ExtrapolateToZ(Double_t z, TVector3& position) const {
  if (std::abs(m_pz) < 1e-10) {
    return false;
  }
  const Double_t lambda = (z - m_z) / m_pz;
  position.SetXYZ(m_x + lambda * m_px, m_y + lambda * m_py, z);
  return true;
}

}  // namespace SHiP
