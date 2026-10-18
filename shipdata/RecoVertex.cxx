// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "RecoVertex.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace SHiP {

RecoVertex::RecoVertex(const TVector3& position,
                       const std::array<Double_t, 6>& covariance, Double_t chi2,
                       Double_t nDoF)
    : TObject(),
      m_x(position.X()),
      m_y(position.Y()),
      m_z(position.Z()),
      m_err_x(std::sqrt(std::max(0.0, covariance[0]))),
      m_err_y(std::sqrt(std::max(0.0, covariance[3]))),
      m_err_z(std::sqrt(std::max(0.0, covariance[5]))),
      m_chi2(chi2),
      m_nDoF(nDoF),
      m_cov_elements(covariance.begin(), covariance.end()) {}

void RecoVertex::AddTrack(Int_t trackId, const TVector3& momentum,
                          const std::array<Double_t, 6>& momentumCovariance) {
  m_trackIds.push_back(trackId);
  m_trackPx.push_back(momentum.X());
  m_trackPy.push_back(momentum.Y());
  m_trackPz.push_back(momentum.Z());
  m_trackCovP.insert(m_trackCovP.end(), momentumCovariance.begin(),
                     momentumCovariance.end());
}

std::array<Double_t, 6> RecoVertex::GetTrackMomentumCovariance(size_t i) const {
  if (i >= m_trackIds.size()) {
    throw std::out_of_range("RecoVertex: track index out of range");
  }
  std::array<Double_t, 6> covariance{};
  std::copy_n(m_trackCovP.begin() + 6 * i, 6, covariance.begin());
  return covariance;
}

}  // namespace SHiP
