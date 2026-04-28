// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_GENERATOR_H_
#define SHIPGEN_GENERATOR_H_

#include <cmath>
#include <optional>
#include <string>
#include <vector>

#include "FairGenerator.h"
#include "FairLogger.h"

namespace SHiP {
class Generator : public FairGenerator {
 public:
  using FairGenerator::Init;
  Generator() {};
  ~Generator() override;

  virtual Bool_t Init(const char*, int) = 0;
  virtual Bool_t Init(const char*) = 0;
  virtual Bool_t Init(const std::vector<std::string>& inFiles,
                      int startNumber) {
    LOG(warning) << "Multiple input files not implemented for this generator "
                    "- only taking the first!";
    return Init(inFiles.at(0).c_str(), startNumber);
  };
  virtual Bool_t Init(const std::vector<std::string>& inFiles) {
    LOG(warning) << "Multiple input files not implemented for this generator "
                    "- only taking the first!";
    return Init(inFiles.at(0).c_str(), 0);
  };

  virtual void UseExternalFile(std::string x, Int_t i) {
    fextFile = x;
    firstEvent = i;
  };

  virtual void UseExternalFile(std::vector<std::string>& inFiles, Int_t i) {
    LOG(warning) << "Multiple external files not implemented for this "
                    "generator - only taking the first!";
    UseExternalFile(inFiles.at(0).c_str(), i);
  }

  /// Set maximum allowed slopes |px/pz| and |py/pz| for vessel acceptance.
  /// Parameters are tan(theta), not angle in radians.
  void SetMaxTheta(Double_t thetaX, Double_t thetaY) {
    fMaxThetaX = thetaX;
    fMaxThetaY = thetaY;
    fUseVesselAcceptance = true;
  };
  Int_t nrOfGeoRejections() const { return fnGeoRejects; }

 protected:
  bool IsInVesselAcceptance(Double_t px, Double_t py, Double_t pz) const {
    if (!fUseVesselAcceptance) return true;
    if (pz <= 0) return false;
    return std::abs(px / pz) < fMaxThetaX && std::abs(py / pz) < fMaxThetaY;
  }

  std::optional<std::string> fextFile;
  Int_t firstEvent = 0;
  Double_t fMaxThetaX = 0;
  Double_t fMaxThetaY = 0;
  bool fUseVesselAcceptance = false;
  Int_t fnGeoRejects = 0;
};
}  // namespace SHiP
#endif  // SHIPGEN_GENERATOR_H_
