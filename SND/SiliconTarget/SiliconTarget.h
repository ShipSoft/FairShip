// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SND_SILICONTARGET_SILICONTARGET_H_
#define SND_SILICONTARGET_SILICONTARGET_H_

#include "Detector.h"
#include "SiliconTargetPoint.h"
#include "TGeoMedium.h"

class FairVolume;

class SiliconTarget : public SHiP::Detector<SiliconTargetPoint> {
 public:
  SiliconTarget(const char* name, Bool_t Active, const char* Title = "");
  SiliconTarget();

  void SetSiliconTargetParameters(Double_t targetWidth, Double_t targetHeight,
                                  Double_t sensorWidth, Double_t sensorLength,
                                  Int_t nLayers, Double_t zPosition,
                                  Double_t targetThickness,
                                  Double_t targetSpacing,
                                  Double_t moduleOffset);

  TGeoVolume* CreateSiliconPlanes(const char* name, Double_t sensorWidth,
                                  Double_t sensorLength, Double_t planeSpacing,
                                  TGeoMedium* material, Int_t layerId);

  void ConstructGeometry() override;

  Bool_t ProcessHits(FairVolume* vol = nullptr) override;

 private:
  Double_t fTargetWidth;
  Double_t fTargetHeight;
  Double_t fSensorWidth;
  Double_t fSensorLength;
  Int_t fLayers;
  Double_t fZPosition;
  Double_t fTargetThickness;
  Double_t fTargetSpacing;
  Double_t fModuleOffset;

  SiliconTarget(const SiliconTarget&) = delete;
  SiliconTarget& operator=(const SiliconTarget&) = delete;
};

#endif  // SND_SILICONTARGET_SILICONTARGET_H_
