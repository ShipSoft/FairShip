// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "splitcal.h"

#include <iostream>

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
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
#include "ShipStack.h"
#include "TCanvas.h"
#include "TClonesArray.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoShapeAssembly.h"
#include "TGeoTube.h"
#include "TParticle.h"
#include "TROOT.h"
#include "TView3D.h"
#include "TVirtualMC.h"
#include "splitcalPoint.h"
using std::cout;
using std::endl;

splitcal::splitcal() : Detector("splitcal", kTRUE, kSplitCal) {}

splitcal::splitcal(const char* name, Bool_t active)
    : Detector(name, active, kSplitCal) {}

Bool_t splitcal::ProcessHits(FairVolume* vol) {
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

  // Create splitcalPoint at exit of active volume
  if (gMC->IsTrackExiting() || gMC->IsTrackStop() ||
      gMC->IsTrackDisappeared()) {
    fEventID = gMC->CurrentEvent();
    fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
    Int_t detID = 0;
    gMC->CurrentVolID(detID);

    fVolumeID = detID;
    if (fELoss == 0.) {
      return kFALSE;
    }
    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    AddHit(fEventID, fTrackID, fVolumeID,
           TVector3(fPos.X(), fPos.Y(), fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, fELoss,
           pdgCode);

    // Increment number of splitcal det points in TParticle
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kSplitCal);
  }

  return kTRUE;
}

void splitcal::SetZStart(Double_t ZStart) { fZStart = ZStart; }
void splitcal::SetEmpty(Double_t Empty, Double_t BigGap,
                        Double_t ActiveECAL_gas_gap,
                        Double_t first_precision_layer,
                        Double_t second_precision_layer,
                        Double_t third_precision_layer,
                        Double_t num_precision_layers) {
  fEmpty = Empty;
  fBigGap = BigGap;
  fActiveECAL_gas_gap = ActiveECAL_gas_gap;
  ffirst_precision_layer = first_precision_layer;
  fsecond_precision_layer = second_precision_layer;
  fthird_precision_layer = third_precision_layer;
  fnum_precision_layers = num_precision_layers;
}

void splitcal::SetThickness(Double_t ActiveECALThickness,
                            Double_t ActiveHCALThickness,
                            Double_t FilterECALThickness,
                            Double_t FilterECALThickness_first,
                            Double_t FilterHCALThickness,
                            Double_t ActiveECAL_gas_Thickness) {
  fActiveECALThickness = ActiveECALThickness;
  fActiveHCALThickness = ActiveHCALThickness;
  fFilterECALThickness = FilterECALThickness;
  fFilterECALThickness_first = FilterECALThickness_first;
  fFilterHCALThickness = FilterHCALThickness;
  fActiveECAL_gas_Thickness = ActiveECAL_gas_Thickness;
}
void splitcal::SetMaterial(Double_t ActiveECALMaterial,
                           Double_t ActiveHCALMaterial,
                           Double_t FilterECALMaterial,
                           Double_t FilterHCALMaterial) {
  fActiveECALMaterial = ActiveECALMaterial;
  fActiveHCALMaterial = ActiveHCALMaterial;
  fFilterECALMaterial = FilterECALMaterial;
  fFilterHCALMaterial = FilterHCALMaterial;
}

void splitcal::SetNSamplings(Int_t nECALSamplings, Int_t nHCALSamplings,
                             Double_t ActiveHCAL) {
  fnHCALSamplings = nHCALSamplings;
  fnECALSamplings = nECALSamplings;
  fActiveHCAL = ActiveHCAL;
}

void splitcal::SetNModules(Int_t nModulesInX, Int_t nModulesInY) {
  fNModulesInX = nModulesInX;
  fNModulesInY = nModulesInY;
}

void splitcal::SetNStrips(Int_t nStrips) { fNStripsPerModule = nStrips; }

void splitcal::SetStripSize(Double_t stripHalfWidth, Double_t stripHalfLength) {
  fStripHalfWidth = stripHalfWidth;
  fStripHalfLength = stripHalfLength;
}

void splitcal::SetXMax(Double_t xMax) { fXMax = xMax; }
void splitcal::SetYMax(Double_t yMax) { fYMax = yMax; }
void splitcal::ConstructGeometry() {
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */

  TGeoVolume* top = gGeoManager->GetTopVolume();
  TGeoVolume* tSplitCal = new TGeoVolumeAssembly("SplitCalDetector");

  ShipGeo::InitMedium("iron");
  ShipGeo::InitMedium("lead");
  ShipGeo::InitMedium("Scintillator");
  ShipGeo::InitMedium("argon");
  ShipGeo::InitMedium("GEMmixture");

  TGeoMedium* A2 = gGeoManager->GetMedium("iron");
  TGeoMedium* A3 = gGeoManager->GetMedium("lead");
  TGeoMedium* A4 = gGeoManager->GetMedium("GEMmixture");
  TGeoMedium* A1 = gGeoManager->GetMedium("Scintillator");

  Double_t zStartSplitCal = fZStart;

  TGeoVolume* newECALfilter_first;  // first layer can have different thickeness
  TGeoVolume* newECALfilter;
  TGeoVolume* newECALdet_gas;
  TGeoVolume* stripGivingX;
  TGeoVolume* stripGivingY;

  TGeoVolume* newHCALfilter[100];
  TGeoVolume* newHCALdet[100];
  const char* char_labelHCALfilter[100];
  TString labelHCALfilter;
  const char* char_labelHCALdet[100];
  TString labelHCALdet;

  Double_t z_splitcal = 0;

  // logical volume for the absorbing layers
  // first absorbing layer can have different thinkens from the others
  newECALfilter_first = gGeoManager->MakeBox(
      "ECALfilter_first", A3, fXMax, fYMax, fFilterECALThickness_first / 2);
  newECALfilter_first->SetLineColor(kGray);
  newECALfilter = gGeoManager->MakeBox("ECALfilter", A3, fXMax, fYMax,
                                       fFilterECALThickness / 2);
  newECALfilter->SetLineColor(kGray);

  stripGivingX =
      gGeoManager->MakeBox("stripGivingX", A1, fStripHalfWidth,
                           fStripHalfLength, fActiveECALThickness / 2);
  stripGivingX->SetVisibility(kTRUE);
  AddSensitiveVolume(stripGivingX);
  stripGivingX->SetLineColor(kGreen);

  stripGivingY =
      gGeoManager->MakeBox("stripGivingY", A1, fStripHalfLength,
                           fStripHalfWidth, fActiveECALThickness / 2);
  stripGivingY->SetVisibility(kTRUE);
  AddSensitiveVolume(stripGivingY);
  stripGivingY->SetLineColor(kGreen);

  // logical volume for the high precision sensitive layers
  newECALdet_gas = gGeoManager->MakeBox("ECALdet_gas", A4, fXMax, fYMax,
                                        fActiveECAL_gas_Thickness / 2);
  AddSensitiveVolume(newECALdet_gas);
  newECALdet_gas->SetLineColor(kRed);

  // now position layer volumes in tSplitCal mother volume
  for (Int_t i_nlayECAL = 0; i_nlayECAL < fnECALSamplings; i_nlayECAL++) {
    // position absorber layers
    // thinkness of first layer can be different from others
    if (i_nlayECAL == 0) {
      z_splitcal += fFilterECALThickness_first / 2;
      tSplitCal->AddNode(newECALfilter_first, i_nlayECAL * 1e5,
                         new TGeoTranslation(0, 0, z_splitcal));
      z_splitcal += fFilterECALThickness_first / 2;
    } else {
      z_splitcal += fFilterECALThickness / 2;
      tSplitCal->AddNode(newECALfilter, i_nlayECAL * 1e5,
                         new TGeoTranslation(0, 0, z_splitcal));
      z_splitcal += fFilterECALThickness / 2;
    }

    if (i_nlayECAL == 0)
      z_splitcal += fEmpty;  // space after first layer? set to 0 in the
                             // config file? for whar is it for?
    if (i_nlayECAL == 7) z_splitcal += fBigGap;

    // position high precision sensitive layers
    if (i_nlayECAL == ffirst_precision_layer ||
        i_nlayECAL == fsecond_precision_layer ||
        i_nlayECAL == fthird_precision_layer) {
      z_splitcal += fActiveECAL_gas_Thickness / 2;

      tSplitCal->AddNode(newECALdet_gas, 1e8 + (i_nlayECAL + 1) * 1e5,
                         new TGeoTranslation(0, 0, z_splitcal));
      z_splitcal += fActiveECAL_gas_Thickness / 2;
      if (fnum_precision_layers == 2) {
        z_splitcal += fActiveECAL_gas_gap;
        z_splitcal += fActiveECAL_gas_Thickness / 2;
        tSplitCal->AddNode(newECALdet_gas, 1e8 + (i_nlayECAL + 1) * 1e5,
                           new TGeoTranslation(0, 0, z_splitcal));
        z_splitcal += fActiveECAL_gas_Thickness / 2;
      }
    } else {
      // position sensitive layers
      z_splitcal += fActiveECALThickness / 2;
      if (i_nlayECAL % 2 == 0) {
        // strips giving x information
        for (int mx = 0; mx < fNModulesInX; mx++) {
          for (int my = 0; my < fNModulesInY; my++) {
            for (int j = 0; j < fNStripsPerModule; j++) {
              int index = (i_nlayECAL + 1) * 1e5 + (mx + 1) * 1e4 +
                          (my + 1) * 1e3 + j + 1;
              double xCoordinate =
                  -fXMax + (fNStripsPerModule * mx + j + 0.5) *
                               fStripHalfWidth *
                               2;  // the times 2 is to get the total width
                                   // from the half-width
              double yCoordinate =
                  -fYMax + (my + 0.5) * fStripHalfLength *
                               2;  // the times 2 is to get the total length
                                   // from the half-length
              tSplitCal->AddNode(
                  stripGivingX, index,
                  new TGeoTranslation(xCoordinate, yCoordinate, z_splitcal));

            }  // end loop on strips
          }  // end loop on modules in y
        }  // end loop on modules in x
      }  // end layer stripped in X
      else {
        // strips giving y information
        for (int mx = 0; mx < fNModulesInX; mx++) {
          for (int my = 0; my < fNModulesInY; my++) {
            for (int j = 0; j < fNStripsPerModule; j++) {
              int index = (i_nlayECAL + 1) * 1e5 + (mx + 1) * 1e4 +
                          (my + 1) * 1e3 + j + 1;
              double xCoordinate =
                  -fXMax + (mx + 0.5) * fStripHalfLength *
                               2;  // the times 2 is to get the total length
                                   // from the half-length
              double yCoordinate =
                  -fYMax + (fNStripsPerModule * my + j + 0.5) *
                               fStripHalfWidth *
                               2;  // the times 2 is to get the total width
                                   // from the half-width
              tSplitCal->AddNode(
                  stripGivingY, index,
                  new TGeoTranslation(xCoordinate, yCoordinate, z_splitcal));

            }  // end loop on strips
          }  // end loop on modules in y
        }  // end loop on modules in x
      }  // end layer stripped in Y

      z_splitcal += fActiveECALThickness / 2;
    }  // end loop on sensitive scintillator layers

  }  // end loop in ecal layers

  for (Int_t i_nlayHCAL = 0; i_nlayHCAL < 1; i_nlayHCAL++) {
    labelHCALfilter = "HCALfilter_";
    labelHCALfilter += i_nlayHCAL;
    char_labelHCALfilter[i_nlayHCAL] = labelHCALfilter;
    labelHCALdet = "HCAL_det";
    labelHCALdet += i_nlayHCAL;
    char_labelHCALdet[i_nlayHCAL] = labelHCALdet;
    newHCALfilter[i_nlayHCAL] =
        gGeoManager->MakeBox(char_labelHCALfilter[i_nlayHCAL], A2, fXMax, fYMax,
                             fFilterHCALThickness / 2);
    if (fActiveHCAL) {
      newHCALdet[i_nlayHCAL] =
          gGeoManager->MakeBox(char_labelHCALdet[i_nlayHCAL], A4, fXMax, fYMax,
                               fActiveHCALThickness / 2);

      AddSensitiveVolume(newHCALdet[i_nlayHCAL]);

      newHCALdet[i_nlayHCAL]->SetLineColor(kRed);
    }
    newHCALfilter[i_nlayHCAL]->SetLineColor(kBlue);
  }
  for (Int_t i_nlayHCAL = 0; i_nlayHCAL < fnHCALSamplings; i_nlayHCAL++) {
    z_splitcal += fFilterHCALThickness / 2;
    tSplitCal->AddNode(newHCALfilter[i_nlayHCAL], 1,
                       new TGeoTranslation(0, 0, z_splitcal));
    z_splitcal += fFilterHCALThickness / 2;

    z_splitcal += fActiveHCALThickness / 2;
    if (fActiveHCAL)
      tSplitCal->AddNode(newHCALdet[i_nlayHCAL], 1,
                         new TGeoTranslation(0, 0, z_splitcal));
    z_splitcal += fActiveHCALThickness / 2;
  }

  // finish assembly and position
  TGeoShapeAssembly* asmb =
      dynamic_cast<TGeoShapeAssembly*>(tSplitCal->GetShape());
  Double_t totLength = asmb->GetDZ();
  top->AddNode(tSplitCal, 1,
               new TGeoTranslation(0, 0, zStartSplitCal + totLength));
}
