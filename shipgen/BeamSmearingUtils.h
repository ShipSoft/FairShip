// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef SHIPGEN_BEAMSMEARINGUTILS_H_
#define SHIPGEN_BEAMSMEARINGUTILS_H_

#include "Rtypes.h"

#include <utility>

/**
 * Calculate beam smearing and painting offsets
 * @param smearBeam   Standard deviation for Gaussian smearing (in units appropriate for the generator)
 * @param paintBeam   Radius for uniform circular painting (in units appropriate for the generator)
 * @return std::pair<Double_t, Double_t> containing (dx, dy) offsets in same units as input parameters
 */
std::pair<Double_t, Double_t> CalculateBeamOffset(Double_t smearBeam, Double_t paintBeam);

#endif   // SHIPGEN_BEAMSMEARINGUTILS_H_
