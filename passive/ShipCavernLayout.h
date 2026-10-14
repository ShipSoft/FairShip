// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef PASSIVE_SHIPCAVERNLAYOUT_H_
#define PASSIVE_SHIPCAVERNLAYOUT_H_

#include "Rtypes.h"
#include "ShipUnit.h"

/**
 * Cross-sections of the TCC8 tunnel and the ECN3 hall (cm, beam axis at
 * x = y = 0).
 *
 * Inner concrete surfaces of the civil-engineering solid in the CAD model
 * ST1967028_01 behind the integration layout SPSXXSHIP0002 version 2026-0.1
 * (EDMS 3287817 v1.1), sectioned across the beam. The walls drift by
 * 0.35 mrad against the beam; the values are taken at mid-tunnel and
 * mid-hall. Not modelled: the TCC8 arch upstream of z = 6.2 m, the ECN3 crane
 * ledges above y = 5.84 m and the ECN3 arch above the springline.
 */
namespace ShipCavernLayout {
// TCC8: flat ceiling, the underside of the slab downstream of z = 6.2 m
inline const Double_t kTCC8LeftX = -3.587 * ShipUnit::m;
inline const Double_t kTCC8RightX = 6.413 * ShipUnit::m;
inline const Double_t kTCC8FloorY = -1.703 * ShipUnit::m;
inline const Double_t kTCC8CeilingY = 5.761 * ShipUnit::m;
// Stair step between TCC8 and ECN3, at the TCC8 width and ceiling
inline const Double_t kStairFloorY = -2.503 * ShipUnit::m;
// ECN3, up to the arch springline
inline const Double_t kECN3LeftX = -4.566 * ShipUnit::m;
inline const Double_t kECN3RightX = 11.434 * ShipUnit::m;
inline const Double_t kECN3FloorY = -3.364 * ShipUnit::m;
inline const Double_t kECN3SpringlineY = 8.636 * ShipUnit::m;
}  // namespace ShipCavernLayout

#endif  // PASSIVE_SHIPCAVERNLAYOUT_H_
