// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "DetectorHit.h"

namespace SHiP {

// -----   Default constructor   -------------------------------------------
DetectorHit::DetectorHit() : TObject(), fdigi(0), fDetectorID(-1) {}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
DetectorHit::DetectorHit(Int_t detID, Float_t digi)
    : TObject(), fdigi(digi), fDetectorID(detID) {}

}  // namespace SHiP
