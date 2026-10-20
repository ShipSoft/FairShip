// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "CaloScoringPlane.h"

#include "ShipDetectorList.h"

CaloScoringPlane::CaloScoringPlane()
    : ScoringPlane("CaloScoringPlane", kTRUE, kCaloScoringPlane) {
  fLineColor = kOrange;
}

CaloScoringPlane::CaloScoringPlane(const char* name, Bool_t active)
    : ScoringPlane(name, active, kCaloScoringPlane) {
  fLineColor = kOrange;
}

void CaloScoringPlane::ConstructGeometry() {
  // A single plane on the beam axis, set by SetZposition and SetBoxDimensions.
  AddPlane("CaloScoringPlane", 0., 0., fZPos, fXSize, fYSize, fZSize);
  ScoringPlane::ConstructGeometry();
}
