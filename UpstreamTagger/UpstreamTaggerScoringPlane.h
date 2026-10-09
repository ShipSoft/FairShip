// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPLANE_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPLANE_H_

#include <vector>

#include "Detector.h"
#include "UpstreamTaggerScoringPoint.h"

class FairVolume;

/**
 * @brief Thin vacuum scoring planes upstream of the decay vessel
 *
 * Every track entering a plane produces one UpstreamTaggerScoringPoint,
 * independent of energy deposit, so the flux reaching the decay vessel can be
 * compared with what the UBT sees. Planes added with muonsOnly record only
 * mu+-. The point detID is the plane number, counted from 1 in the order the
 * planes were added.
 */
class UpstreamTaggerScoringPlane
    : public SHiP::Detector<UpstreamTaggerScoringPoint> {
 public:
  UpstreamTaggerScoringPlane(const char* Name, Bool_t Active);

  /** default constructor */
  UpstreamTaggerScoringPlane();

  /** Called for each step inside the plane */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  /** Adds a plane of full size sizeX x sizeY centred at (x, y, z) */
  void AddPlane(Double_t x, Double_t y, Double_t z, Double_t sizeX,
                Double_t sizeY, Bool_t muonsOnly = kFALSE) {
    fPlanes.push_back({x, y, z, sizeX, sizeY, muonsOnly});
  }
  /** Sets the thickness shared by all planes */
  void SetPlaneThickness(Double_t z) { fSizeZ = z; }

  /** Create the detector geometry */
  void ConstructGeometry() override;

 private:
  struct Plane {
    Double_t x;        // x-position of the plane centre
    Double_t y;        // y-position of the plane centre
    Double_t z;        // z-position of the plane centre
    Double_t sizeX;    // plane width
    Double_t sizeY;    // plane height
    Bool_t muonsOnly;  // record only mu+-
  };
  std::vector<Plane> fPlanes;  //! planes, detID = index + 1
  Double_t fSizeZ = 0.;        //! plane thickness, set from the
                               //! geometry configuration

  UpstreamTaggerScoringPlane(const UpstreamTaggerScoringPlane&) = delete;
  UpstreamTaggerScoringPlane& operator=(const UpstreamTaggerScoringPlane&) =
      delete;
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPLANE_H_
