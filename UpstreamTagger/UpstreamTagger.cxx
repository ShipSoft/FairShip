// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTagger.h"

#include <cmath>
#include <iostream>
#include <map>

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
  // Set parameters at entrance of volume, or at the first step of a track
  // created inside it (e.g. a delta ray). Reset ELoss.
  if (gMC->IsTrackEntering() || gMC->IsNewTrack()) {
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
    fELoss = 0.;

    // Increment number of veto det points in TParticle
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kUpstreamTagger);
  }

  return kTRUE;
}

void UpstreamTagger::ConstructGeometry() {
  TGeoVolume* top = gGeoManager->GetTopVolume();

  ShipGeo::InitMedium("Scintillator");
  TGeoMedium* scintillator = gGeoManager->GetMedium("Scintillator");
  if (!scintillator) {
    Fatal("ConstructGeometry", "Medium 'Scintillator' not found.");
  }
  if (fRegions.empty()) {
    Fatal("ConstructGeometry", "No regions loaded from the UBT detector map.");
  }
  if (fSizeX <= 0. || fSizeY <= 0. || fEnvelopeZ <= 0.) {
    Fatal("ConstructGeometry", "UBT box dimensions not set.");
  }

  fDetector = new TGeoVolumeAssembly("Upstream_Tagger");

  std::map<Double_t, Int_t> regionsPerTileSize;
  for (const Region& region : fRegions) {
    if (region.sizeX <= 0. || region.sizeY <= 0.) {
      Fatal("ConstructGeometry", "UBT region %d has a non-positive size.",
            region.id);
    }
    if (region.thickness <= 0. || region.thickness > fEnvelopeZ) {
      Fatal("ConstructGeometry",
            "UBT region %d: the thickness %g cm of its %g cm tiles is not in "
            "(0, %g] cm, the space reserved for the UBT.",
            region.id, region.thickness, region.constituentTileSize,
            fEnvelopeZ);
    }
    if (std::abs(region.x - fCenterX) + region.sizeX / 2. > fSizeX / 2. ||
        std::abs(region.y - fCenterY) + region.sizeY / 2. > fSizeY / 2.) {
      Fatal("ConstructGeometry", "UBT region %d lies outside the UBT box.",
            region.id);
    }
    const TString volumeName =
        TString::Format("UpstreamTaggerRegion%d_%dcm", region.id,
                        static_cast<Int_t>(region.constituentTileSize));
    TGeoVolume* regionVolume =
        gGeoManager->MakeBox(volumeName, scintillator, region.sizeX / 2.,
                             region.sizeY / 2., region.thickness / 2.);
    // A shade of blue per tile size in the event display.
    regionVolume->SetLineColor(kBlue -
                               static_cast<Int_t>(region.constituentTileSize));
    AddSensitiveVolume(regionVolume);
    fDetector->AddNode(regionVolume, region.id,
                       new TGeoTranslation(region.x, region.y, 0.));
    ++regionsPerTileSize[region.constituentTileSize];
  }

  top->AddNode(fDetector, 1, new TGeoTranslation(0., 0., det_zPos));
  cout << " Z Position (Upstream Tagger) " << det_zPos << ", "
       << fRegions.size() << " mapped regions (";
  for (auto it = regionsPerTileSize.begin(); it != regionsPerTileSize.end();
       ++it) {
    cout << (it == regionsPerTileSize.begin() ? "" : ", ") << it->second
         << " with " << it->first << " cm tiles";
  }
  cout << ")" << endl;
}
