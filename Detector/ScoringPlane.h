// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef DETECTOR_SCORINGPLANE_H_
#define DETECTOR_SCORINGPLANE_H_

#include <algorithm>
#include <cstdlib>
#include <string>
#include <vector>

#include "Detector.h"
#include "FairLogger.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
#include "ShipStack.h"
#include "TGeoManager.h"
#include "TGeoMatrix.h"
#include "TGeoMedium.h"
#include "TParticle.h"
#include "TVector3.h"
#include "TVirtualMC.h"

namespace SHiP {

/**
 * @brief Thin vacuum planes that record every track entering them
 *
 * Shared by CaloScoringPlane and UpstreamTaggerScoringPlane, which differ only
 * in their point type (and so their output branch) and detector ID.
 *
 * Every track entering a plane produces one point holding the MC-truth
 * position, momentum, time and PDG code, with zero energy loss. No energy
 * deposit is required (the medium is vacuum), so neutral particles are
 * recorded too. Position, momentum and time are those at the end of the
 * track's first step in the plane. A track crossing a plane twice (e.g.
 * back-scattered) gives two points; the sign of Pz tells the direction.
 *
 * The point detector ID is the copy number of the plane: its index + 1, in
 * the order the planes were added. A plane can be restricted to some species,
 * given by their absolute PDG codes.
 */
template <typename PointType>
class ScoringPlane : public Detector<PointType> {
 public:
  using Detector<PointType>::Detector;

  /** Adds a plane: the name of its volume, its centre and full sizes (cm),
   * and, if not empty, the absolute PDG codes of the only particles it
   * records */
  void AddPlane(const char* name, Double_t x, Double_t y, Double_t z,
                Double_t sizeX, Double_t sizeY, Double_t sizeZ,
                const std::vector<Int_t>& absPdgCodes = {}) {
    fPlanes.push_back({name, x, y, z, sizeX, sizeY, sizeZ, absPdgCodes});
  }

  Bool_t ProcessHits(FairVolume* /*vol*/ = nullptr) override {
    // Score each track once, on its first step in the plane.
    if (!gMC->IsTrackEntering()) {
      return kFALSE;
    }
    Int_t copyNo = 0;
    gMC->CurrentVolID(copyNo);
    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    const Int_t pdgCode = p->GetPdgCode();
    const std::vector<Int_t>& accepted = fPlanes[copyNo - 1].absPdgCodes;
    if (!accepted.empty() && std::find(accepted.begin(), accepted.end(),
                                       std::abs(pdgCode)) == accepted.end()) {
      return kFALSE;
    }

    this->fEventID = gMC->CurrentEvent();
    this->fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
    this->fVolumeID = copyNo;
    this->fTime = gMC->TrackTime() * 1.0e09;  // ns
    this->fLength = gMC->TrackLength();
    gMC->TrackPosition(this->fPos);
    gMC->TrackMomentum(this->fMom);
    this->AddHit(this->fEventID, this->fTrackID, this->fVolumeID,
                 TVector3(this->fPos.X(), this->fPos.Y(), this->fPos.Z()),
                 TVector3(this->fMom.Px(), this->fMom.Py(), this->fMom.Pz()),
                 this->fTime, this->fLength, 0., pdgCode);

    // Count a point for this track. ShipStack only keeps a secondary because
    // of its points when it is configured with a minimum number of points
    // (MCTracksWithHitsOnly / MCTracksWithHitsOrEnergyCut in
    // run_simScript.py). With the default MCTracksWithEnergyCutOnly,
    // secondaries below the energy cut are dropped and their points get track
    // ID -2.
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(static_cast<DetectorId>(this->GetDetId()));
    return kTRUE;
  }

  void ConstructGeometry() override {
    TGeoVolume* top = gGeoManager->GetTopVolume();
    ShipGeo::InitMedium("vacuum");
    TGeoMedium* vacuum = gGeoManager->GetMedium("vacuum");
    if (!vacuum) {
      LOG(fatal) << this->GetName() << ": medium 'vacuum' not found.";
    }
    if (fPlanes.empty()) {
      LOG(fatal) << this->GetName() << ": no scoring planes.";
    }

    for (size_t i = 0; i < fPlanes.size(); ++i) {
      const Plane& pl = fPlanes[i];
      if (pl.sizeX <= 0. || pl.sizeY <= 0. || pl.sizeZ <= 0.) {
        LOG(fatal) << this->GetName() << ": invalid dimensions of " << pl.name;
      }
      TGeoVolume* plane = gGeoManager->MakeBox(
          pl.name.c_str(), vacuum, pl.sizeX / 2., pl.sizeY / 2., pl.sizeZ / 2.);
      plane->SetLineColor(fLineColor);
      this->AddSensitiveVolume(plane);
      // The copy number, i + 1, is the point detector ID: node <name>_<i + 1>.
      top->AddNode(plane, i + 1, new TGeoTranslation(pl.x, pl.y, pl.z));
      this->fDetector = plane;
      LOG(info) << pl.name << ": " << pl.sizeX << " x " << pl.sizeY << " x "
                << pl.sizeZ << " cm3 centred at (" << pl.x << ", " << pl.y
                << ", " << pl.z << ") cm"
                << (pl.absPdgCodes.empty() ? "" : ", PDG-filtered");
    }
  }

 protected:
  Color_t fLineColor = kGray;  //! colour of the planes in the event display

 private:
  struct Plane {
    std::string name;                // volume name
    Double_t x, y, z;                // centre (cm)
    Double_t sizeX, sizeY, sizeZ;    // full sizes (cm)
    std::vector<Int_t> absPdgCodes;  // if not empty, the only species recorded
  };
  std::vector<Plane> fPlanes;  //! planes, detector ID = index + 1
};

}  // namespace SHiP

#endif  // DETECTOR_SCORINGPLANE_H_
