// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_PYTHIAUNITS_H_
#define SHIPGEN_PYTHIAUNITS_H_

#include "ShipUnit.h"

namespace shipgen {

/// Pythia8 lengths are in mm, FairShip lengths in cm.
constexpr double kPythiaLengthPerCm = 10.;
/// Speed of light in cm/s, for VMC times in seconds.
constexpr double kCLightCmPerS = ShipUnit::c_light * ShipUnit::s;

/// A Pythia8 position (mm) in FairShip units (cm).
constexpr double PythiaLengthToCm(double x) { return x / kPythiaLengthPerCm; }
/// A Pythia8 time (mm/c) in VMC units (s).
constexpr double PythiaTimeToS(double t) {
  return t / kPythiaLengthPerCm / kCLightCmPerS;
}

}  // namespace shipgen

#endif  // SHIPGEN_PYTHIAUNITS_H_
