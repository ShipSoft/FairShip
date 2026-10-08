// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTaggerScoringPlane.h"

#include <cstdlib>

#include "FairLogger.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
#include "ShipStack.h"
#include "TGeoManager.h"
#include "TGeoMedium.h"
#include "TParticle.h"
#include "TVector3.h"
#include "TVirtualMC.h"

UpstreamTaggerScoringPlane::UpstreamTaggerScoringPlane()
    : Detector("UpstreamTaggerScoringPlane", kTRUE,
               kUpstreamTaggerScoringPlane) {}

UpstreamTaggerScoringPlane::UpstreamTaggerScoringPlane(const char* name,
                                                       Bool_t active)
    : Detector(name, active, kUpstreamTaggerScoringPlane) {}

Bool_t UpstreamTaggerScoringPlane::ProcessHits(FairVolume* /*vol*/) {
  /** Record each track once, where it enters the plane */
  if (!gMC->IsTrackEntering()) {
    return kFALSE;
  }
  Int_t detID;
  gMC->CurrentVolID(detID);
  TParticle* p = gMC->GetStack()->GetCurrentTrack();
  if (fPlanes[detID - 1].muonsOnly && std::abs(p->GetPdgCode()) != 13) {
    return kFALSE;
  }

  fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
  fEventID = gMC->CurrentEvent();
  fTime = gMC->TrackTime() * 1.0e09;
  fLength = gMC->TrackLength();
  gMC->TrackPosition(fPos);
  gMC->TrackMomentum(fMom);
  AddHit(fEventID, fTrackID, detID, TVector3(fPos.X(), fPos.Y(), fPos.Z()),
         TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, 0.,
         p->GetPdgCode());

  ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
  stack->AddPoint(kUpstreamTaggerScoringPlane);

  return kTRUE;
}

void UpstreamTaggerScoringPlane::ConstructGeometry() {
  TGeoVolume* top = gGeoManager->GetTopVolume();

  ShipGeo::InitMedium("vacuum");
  TGeoMedium* vacuum = gGeoManager->GetMedium("vacuum");
  if (!vacuum) {
    Fatal("ConstructGeometry", "Medium 'vacuum' not found.");
  }
  if (fPlanes.empty() || fSizeZ <= 0.) {
    Fatal("ConstructGeometry", "No UBT scoring planes or invalid thickness.");
  }

  for (size_t i = 0; i < fPlanes.size(); ++i) {
    const Plane& pl = fPlanes[i];
    if (pl.sizeX <= 0. || pl.sizeY <= 0.) {
      Fatal("ConstructGeometry", "Invalid UBT scoring plane dimensions.");
    }
    TGeoVolume* plane =
        gGeoManager->MakeBox(Form("UpstreamTaggerScoringPlane%zu", i + 1),
                             vacuum, pl.sizeX / 2., pl.sizeY / 2., fSizeZ / 2.);
    plane->SetLineColor(kGray);
    AddSensitiveVolume(plane);
    top->AddNode(plane, i + 1, new TGeoTranslation(pl.x, pl.y, pl.z));
    LOG(info) << "UBT scoring plane " << i + 1 << ": " << pl.sizeX << " x "
              << pl.sizeY << " x " << fSizeZ << " cm3 centred at (" << pl.x
              << ", " << pl.y << ", " << pl.z << ") cm"
              << (pl.muonsOnly ? ", muons only" : "");
  }
}
