// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "SiWCalo.h"

#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "ShipGeoUtil.h"
#include "ShipUnit.h"
#include "SiWCaloPoint.h"

// ROOT / TGeo headers
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoTrd1.h"
#include "TGeoTrd2.h"
#include "TGeoVolume.h"
#include "TParticle.h"
#include "TVector3.h"

// FairROOT headers
#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairRootManager.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"
#include "FairVolume.h"

// Additional standard headers
#include "TString.h"  // for TString
#include "TVirtualMC.h"

using namespace ShipUnit;

SiWCalo::SiWCalo()
    : Detector("SiWCalo", kTRUE, kSiWCalo) {}

SiWCalo::SiWCalo(const char* name, Bool_t Active, const char* /*Title*/,
                         Int_t /*DetId*/)
    : Detector(name, Active, kSiWCalo) {}


void SiWCalo::SetSiWCaloParameters(Double_t absWidth, Double_t absHeight,
                                   Double_t sensorWidth, Double_t sensorLength,
                                   Int_t nLayers, Double_t zPosition,
                                   Double_t absThickness,
				   Double_t sensorThickness,
				   Double_t NPixels,
                                   Double_t absSpacing,
                                   Double_t moduleOffset) {
  fAbsWidth = absWidth;
  fAbsHeight = absHeight;
  fSensorWidth = sensorWidth;
  fSensorLength = sensorLength;
  fLayers = nLayers;
  fZPosition = zPosition;
  fAbsThickness = absThickness;
  fSensorThickness = sensorThickness;
  fNPixels = NPixels;
  fAbsSpacing = absSpacing;
  fModuleOffset = moduleOffset;
}

void SiWCalo::CreateSiliconPlane(const char* name,
				 TGeoVolumeAssembly* modMotherVol,
				 Double_t width,
				 Double_t length,
				 Double_t thickness,
				 Double_t NPixels,
				 TGeoMedium* silicon,
				 Int_t layerId) {
  // ------------------------------------------------------------
  // Pixel segmentation
  // ------------------------------------------------------------
  
  Double_t pixX = width / NPixels;
  Double_t pixY = length / NPixels;
  
  auto si_volume = new TGeoVolumeAssembly(Form("%s_sipad", name));
  modMotherVol->AddNode(si_volume, 0, new TGeoTranslation(0, 0, 0));
  auto si_plane = new TGeoVolumeAssembly(Form("%s_sipad_plane", name));
  si_volume->AddNode(si_plane, 0, new TGeoTranslation(0, 0, 0));
  auto pixel = new TGeoBBox(Form("%s_pixel", name), pixX / 2, pixY / 2,
                           thickness / 2);
  auto pixelVol = new TGeoVolume(Form("%s_pixelVol", name), pixel, silicon);
  pixelVol->SetLineColor(kRed);
  pixelVol->SetTransparency(40);
  AddSensitiveVolume(pixelVol);

  for (Int_t i = 0; i < NPixels; i++) {
    for (Int_t j = 0; j < NPixels; j++) {
      Double_t x = -width / 2 + pixX * (i + 0.5);
      Double_t y = -length / 2 + pixY * (j + 0.5);
      si_plane->AddNode(pixelVol, 1e8 + 1e6 + i * NPixels + j,
			new TGeoTranslation(x, y, 0));
    }
  }                

}

void SiWCalo::ConstructGeometry() {
  ShipGeo::InitMedium("tungstenalloySND");
  TGeoMedium* tungsten = gGeoManager->GetMedium("tungstenalloySND");
  ShipGeo::InitMedium("air");
  TGeoMedium* air = gGeoManager->GetMedium("air");
  ShipGeo::InitMedium("silicon");
  TGeoMedium* Silicon = gGeoManager->GetMedium("silicon");

  // TODO: Add full real material sandwich

  Double_t totalLength = fLayers * fAbsSpacing;

  // --- Create an envelope volume for the detector (green, semi-transparent)
  // ---
  auto envBox = new TGeoBBox("SiWCalo_env", fAbsWidth / 2.,
                             fAbsHeight / 2., totalLength / 2.);
  auto envVol = new TGeoVolume("SiWCalo", envBox, air);
  envVol->SetLineColor(kGreen);
  envVol->SetTransparency(50);

  auto absorber = new TGeoBBox("Absorber", fAbsWidth / 2., fAbsHeight / 2.,
                             fAbsThickness / 2.);
  auto absVol = new TGeoVolume("AbsorberVol", absorber, tungsten);
  absVol->SetLineColor(kGray);
  absVol->SetTransparency(40);

  // Define a layer for the SciFi module
  TGeoVolumeAssembly* sensitiveModule = new TGeoVolumeAssembly("SiPad_layer");
  CreateSiliconPlane("SiPadPlane",sensitiveModule,
		     fSensorWidth, fSensorLength,fSensorThickness,
		     fNPixels,
		     Silicon, 1);

  // --- Assemble the layers into the envelope ---
  
  for (Int_t i = 0; i < fLayers; i++) {
    // Compute the center position (z) for the current W layer
    Double_t zPos = -totalLength / 2 + i * fAbsSpacing;
    
    // Place the tungsten layer
    envVol->AddNode(absVol, i,
                    new TGeoTranslation(0, 0, zPos + fAbsThickness / 2.));
    // Place the sensitive module (SciFi + Scintillator) at the correct z
    // position
    envVol->AddNode(sensitiveModule, i,
		    new TGeoTranslation(0, 0, zPos + fAbsThickness + fModuleOffset + fSensorThickness / 2.));
  }

  // Finally, add the envelope to the top volume with the global z offset
  // fZCenter
  gGeoManager->GetTopVolume()->AddNode(envVol, 1,
                                       new TGeoTranslation(0, 0, fZPosition));
}

Bool_t SiWCalo::ProcessHits(FairVolume* vol) {
  /** This method is called from the MC stepping */
  // Set parameters at entrance of volume. Reset ELoss.
  if (gMC->IsTrackEntering()) {
    fELoss = 0.;
    fTime = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    Int_t vol_local_id = nav->GetCurrentNode()->GetNumber() %
      1000000;  // Local ID within the mat or scint.
    Int_t layer_id = nav->GetMother(3)->GetNumber();  // Get layer ID.
    fVolumeID = 100000000 + layer_id * 1000000 +
                vol_local_id;  // 1e8 + layer_id * 1e6 + pixel_local_id;
 
  }

  // Sum energy loss for all steps in the active volume
  fELoss += gMC->Edep();

  // Create SiWCaloPoint at exit of active volume
  if (gMC->IsTrackExiting() || gMC->IsTrackStop() ||
      gMC->IsTrackDisappeared()) {
    if (fELoss == 0.) {
      return kFALSE;
    }

    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);

    Double_t xmean = (fPos.X() + Pos.X()) / 2.;
    Double_t ymean = (fPos.Y() + Pos.Y()) / 2.;
    Double_t zmean = (fPos.Z() + Pos.Z()) / 2.;

    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean, zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, fELoss,
           pdgCode);

    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kSiWCalo);
  }
  return kTRUE;
}

