// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "SiliconTargetHit.h"

#include <iostream>

#include "FairRunSim.h"
#include "ShipUnit.h"
#include "SiliconTarget.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoNavigator.h"
#include "TROOT.h"

SiliconTargetHit::SiliconTargetHit() : ShipHit() { flag = true; }

SiliconTargetHit::SiliconTargetHit(Int_t detID,
                                   const std::vector<SiliconTargetPoint*>& V) {
  // Set detectorID.
  fDetectorID = detID;

  // Sum up signal from all points within the hit
  std::vector<double> _signals;
  double totalSig = 0;

  for (auto* point : V) {
    _signals.push_back(point->GetEnergyLoss());
    fX = point->GetX();
    fY = point->GetY();
    fZ = point->GetZ();
  }

  for (unsigned i = 0; i < _signals.size(); i++) {
    totalSig += _signals[i];
  }

  fSignal = totalSig;
}
// -----   Destructor   ----------------------------------------------------
SiliconTargetHit::~SiliconTargetHit() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void SiliconTargetHit::Print() {
  std::cout << Form(
      "SiliconTargetHit: Detector ID %d, Layer %d, Plane %d, Module %d, Strip "
      "%d, Signal %.2f \n",
      fDetectorID, GetLayer(), GetPlane(), GetModule(), GetStrip(),
      GetSignal());
}
