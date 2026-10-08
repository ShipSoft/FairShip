// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTagger.h"

#include <cmath>
#include <iostream>

#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
#include "ShipStack.h"
#include "TGeoManager.h"
#include "TGeoMedium.h"
#include "TParticle.h"
#include "TString.h"
#include "TVector3.h"
#include "TVirtualMC.h"
#include "UpstreamTaggerPoint.h"
using std::cout;
using std::endl;

UpstreamTagger::UpstreamTagger()
    : Detector("UpstreamTagger", kTRUE, kUpstreamTagger), det_zPos(0) {}

UpstreamTagger::UpstreamTagger(const char* name, Bool_t active)
    : Detector(name, active, kUpstreamTagger), det_zPos(0) {}

Bool_t UpstreamTagger::ProcessHits(FairVolume* vol) {
  /** This method is called from the MC stepping */
  // Set parameters at entrance of volume. Reset ELoss.
  if (gMC->IsTrackEntering()) {
    fELoss = 0.;
    fTime = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
  }

  // Sum energy loss for all steps in the active volume
  fELoss += gMC->Edep();

  // Create vetoPoint at exit of active volume
  if (gMC->IsTrackExiting() || gMC->IsTrackStop() ||
      gMC->IsTrackDisappeared()) {
    if (fELoss == 0.) {
      return kFALSE;
    }

    fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
    fEventID = gMC->CurrentEvent();
    Int_t tileId;
    gMC->CurrentVolID(tileId);

    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X() + Pos.X()) / 2.;
    Double_t ymean = (fPos.Y() + Pos.Y()) / 2.;
    Double_t zmean = (fPos.Z() + Pos.Z()) / 2.;

    AddHit(fEventID, fTrackID, tileId, TVector3(xmean, ymean, zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, fELoss,
           pdgCode, TVector3(Pos.X(), Pos.Y(), Pos.Z()),
           TVector3(Mom.Px(), Mom.Py(), Mom.Pz()));

    // Increment number of veto det points in TParticle
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kUpstreamTagger);
  }

  return kTRUE;
}

void UpstreamTagger::ConstructGeometry() {
  TGeoVolume* top = gGeoManager->GetTopVolume();

  ShipGeo::InitMedium("pterphenyl");
  TGeoMedium* scintillator = gGeoManager->GetMedium("pterphenyl");
  if (!scintillator) {
    Fatal("ConstructGeometry", "Medium 'pterphenyl' not found.");
  }
  if (fRegions.empty()) {
    Fatal("ConstructGeometry", "No regions loaded from the UBT detector map.");
  }
  if (fSmallTileZ <= 0. || fLargeTileZ <= 0. || fSmallTileZ > fEnvelopeZ ||
      fLargeTileZ > fEnvelopeZ) {
    Fatal("ConstructGeometry", "Invalid UBT tile thicknesses.");
  }

  fDetector = new TGeoVolumeAssembly("Upstream_Tagger");

  Int_t smallRegions = 0;
  Int_t bigRegions = 0;
  for (const Region& region : fRegions) {
    const Bool_t isSmall = region.constituentTileSize == 2.;
    if (region.sizeX <= 0. || region.sizeY <= 0. ||
        (!isSmall && region.constituentTileSize != 4.) ||
        std::abs(region.x - fCenterX) + region.sizeX / 2. > fSizeX / 2. ||
        std::abs(region.y - fCenterY) + region.sizeY / 2. > fSizeY / 2.) {
      Fatal("ConstructGeometry", "Invalid entry in the UBT detector map.");
    }
    const TString volumeName =
        TString::Format("UpstreamTaggerRegion%d_%dcm", region.id,
                        static_cast<Int_t>(region.constituentTileSize));
    const Double_t regionThickness = isSmall ? fSmallTileZ : fLargeTileZ;
    TGeoVolume* regionVolume =
        gGeoManager->MakeBox(volumeName, scintillator, region.sizeX / 2.,
                             region.sizeY / 2., regionThickness / 2.);
    regionVolume->SetLineColor(isSmall ? kGreen + 2 : kBlue);
    AddSensitiveVolume(regionVolume);
    fDetector->AddNode(regionVolume, region.id,
                       new TGeoTranslation(region.x, region.y, 0.));
    smallRegions += isSmall;
    bigRegions += !isSmall;
  }

  top->AddNode(fDetector, 1, new TGeoTranslation(0., 0., det_zPos));
  cout << " Z Position (Upstream Tagger) " << det_zPos << ", "
       << fRegions.size() << " mapped regions (" << smallRegions
       << " with 20 x 20 mm2 tiles, " << bigRegions
       << " with 40 x 40 mm2 tiles)" << endl;
}
