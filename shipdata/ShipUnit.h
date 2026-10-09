// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Units of the FairShip C++ code, the same as python/shipunit.py and VMC:
// lengths in cm, energies in GeV and magnetic fields in kilogauss. Times are
// in ns here; VMC (gMC->TrackTime(), FairPrimaryGenerator::AddTrack) uses
// seconds, so a time t in ns is t / ShipUnit::s in seconds.
//
// Multiply a value by its unit to express it in these units, and divide by a
// unit to express a value in that unit. Angles are not defined here: TGeo
// takes degrees, ROOT and the standard library radians. Use TMath for
// physical constants.

#ifndef SHIPDATA_SHIPUNIT_H_
#define SHIPDATA_SHIPUNIT_H_

namespace ShipUnit {

// length
constexpr double cm = 1.;
constexpr double m = 100. * cm;
constexpr double mm = 0.1 * cm;
constexpr double um = 1e-6 * m;
constexpr double km = 1000. * m;

// time
constexpr double ns = 1.;
constexpr double s = 1e9 * ns;

// energy
constexpr double GeV = 1.;
constexpr double MeV = 1e-3 * GeV;
constexpr double keV = 1e-6 * GeV;

// magnetic field
constexpr double kilogauss = 1.;
constexpr double gauss = 1e-3 * kilogauss;
constexpr double tesla = 10. * kilogauss;

// speed of light in vacuum, 29.98 cm/ns
constexpr double c_light = 299792458. * m / s;

}  // namespace ShipUnit

#endif  // SHIPDATA_SHIPUNIT_H_
