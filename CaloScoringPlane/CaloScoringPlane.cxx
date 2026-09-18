// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "CaloScoringPlane.h"

#include "CaloScoringPlanePoint.h"
#include "FairLogger.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
#include "ShipStack.h"
#include "TGeoManager.h"
#include "TGeoMatrix.h"
#include "TGeoMedium.h"
#include "TLorentzVector.h"
#include "TParticle.h"
#include "TVector3.h"
#include "TVirtualMC.h"

CaloScoringPlane::CaloScoringPlane()
    : Detector("CaloScoringPlane", kTRUE, kCaloScoringPlane) {}

CaloScoringPlane::CaloScoringPlane(const char* name, Bool_t active)
    : Detector(name, active, kCaloScoringPlane) {}

Bool_t CaloScoringPlane::ProcessHits(FairVolume* /*vol*/) {
  // Score each track once, on its first step inside the plane (this runs
  // after that step, so the values below are those at its end: the exit face
  // for a particle crossing the plane). Tracks created inside the (vacuum)
  // plane are not scored.
  if (!gMC->IsTrackEntering()) {
    return kFALSE;
  }

  fEventID = gMC->CurrentEvent();
  fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
  Int_t copyNo = 0;
  gMC->CurrentVolID(copyNo);
  fVolumeID = copyNo;

  fTime = gMC->TrackTime() * 1.0e09;  // ns
  fLength = gMC->TrackLength();
  gMC->TrackPosition(fPos);
  gMC->TrackMomentum(fMom);

  TParticle* p = gMC->GetStack()->GetCurrentTrack();
  const Int_t pdgCode = p->GetPdgCode();

  AddHit(fEventID, fTrackID, fVolumeID, TVector3(fPos.X(), fPos.Y(), fPos.Z()),
         TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, 0.,
         pdgCode);

  // Count a point for this track. Note that ShipStack only keeps a secondary
  // because of its points when it is configured with a minimum number of
  // points (MCTracksWithHitsOnly / MCTracksWithHitsOrEnergyCut in
  // run_simScript.py). With the default MCTracksWithEnergyCutOnly, secondaries
  // below the energy cut are dropped and their points get track ID -2.
  ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
  stack->AddPoint(kCaloScoringPlane);

  return kTRUE;
}

void CaloScoringPlane::ConstructGeometry() {
  TGeoVolume* top = gGeoManager->GetTopVolume();

  ShipGeo::InitMedium("vacuum");
  TGeoMedium* vacuum = gGeoManager->GetMedium("vacuum");
  if (!vacuum) {
    Fatal("ConstructGeometry", "Medium 'vacuum' not found.");
  }

  fDetector = gGeoManager->MakeBox("CaloScoringPlane", vacuum, fXSize / 2.,
                                   fYSize / 2., fZSize / 2.);
  fDetector->SetLineColor(kOrange);
  AddSensitiveVolume(fDetector);

  // Node name in the top volume is "CaloScoringPlane_1".
  top->AddNode(fDetector, 1, new TGeoTranslation(0., 0., fZPos));
  LOG(info) << "CaloScoringPlane placed at z = " << fZPos << " cm, size "
            << fXSize << " x " << fYSize << " x " << fZSize << " cm";
}
