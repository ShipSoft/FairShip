// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "SiliconTargetHit.h"

#include <iostream>

#include "FairLogger.h"
#include "FairRunSim.h"
#include "ShipUnit.h"
#include "SiliconTarget.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoNavigator.h"
#include "TROOT.h"

SiliconTargetHit::SiliconTargetHit() : SHiP::DetectorHit() {}

SiliconTargetHit::SiliconTargetHit(Int_t detID,
                                   const std::vector<SiliconTargetPoint*>& V)
    : SHiP::DetectorHit(detID, 0.f) {
  if (V.empty()) {
    LOG(error) << "SiliconTargetHit constructor called with empty point vector";
    return;
  }

  double totalSig = 0;
  for (auto* point : V) {
    totalSig += point->GetEnergyLoss();
    fX = point->GetX();
    fY = point->GetY();
    fZ = point->GetZ();
  }

  fSignal = totalSig;
}
// -----   Public method Print   -------------------------------------------
void SiliconTargetHit::Print() const {
  std::cout << Form(
      "SiliconTargetHit: Detector ID %d, Layer %d, Plane %d, Module %d, Strip "
      "%d, Signal %.2f \n",
      fDetectorID, GetLayer(), GetPlane(), GetModule(), GetStrip(),
      GetSignal());
}
