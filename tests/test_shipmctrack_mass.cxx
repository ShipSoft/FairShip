// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Mass and energy of ShipMCTrack for timelike, massless and spacelike
// particles, and for tracks whose mass was not stored.

#include <cmath>
#include <iostream>
#include <string>

#include "ShipMCTrack.h"
#include "TDatabasePDG.h"
#include "TParticle.h"

namespace {

int failures = 0;

void CheckClose(const std::string& what, double got, double want) {
  const bool ok = std::abs(got - want) <= 1e-5 * std::max(1., std::abs(want));
  std::cout << (ok ? "PASS " : "FAIL ") << what << ": " << got << " (want "
            << want << ")" << std::endl;
  if (!ok) ++failures;
}

ShipMCTrack FromFourVector(int pdg, double px, double py, double pz, double e) {
  TParticle p(pdg, 1, -1, -1, -1, -1, px, py, pz, e, 0., 0., 0., 0.);
  return ShipMCTrack(&p);
}

}  // namespace

int main() {
  // muon: the mass comes from E^2 - P^2
  const double mMu = TDatabasePDG::Instance()->GetParticle(13)->Mass();
  const double pz = 10.;
  const double eMu = std::sqrt(pz * pz + mMu * mMu);
  const ShipMCTrack mu = FromFourVector(13, 0., 0., pz, eMu);
  CheckClose("muon mass", mu.GetMass(), mMu);
  CheckClose("muon energy", mu.GetEnergy(), eMu);

  // real photon
  const ShipMCTrack gamma = FromFourVector(22, 0., 0., pz, pz);
  CheckClose("photon mass", gamma.GetMass(), 0.);
  CheckClose("photon energy", gamma.GetEnergy(), pz);

  // virtual photon, spacelike: negative mass, energy from P^2 - |m|^2
  const double eVirtual = 0.5 * pz;
  const ShipMCTrack virtualGamma = FromFourVector(22, 0., 0., pz, eVirtual);
  CheckClose("spacelike mass", virtualGamma.GetMass(),
             -std::sqrt(pz * pz - eVirtual * eVirtual));
  CheckClose("spacelike energy", virtualGamma.GetEnergy(), eVirtual);

  // mass not stored (default constructor, old files): PDG mass
  const ShipMCTrack noMass(13, -1, 0., 0., pz, -1., 0., 0., 0., 0., 0, 0, 0,
                           1.);
  CheckClose("mass not stored", noMass.GetMass(), mMu);
  CheckClose("energy with mass not stored", noMass.GetEnergy(), eMu);

  std::cout << (failures ? "FAILED" : "ALL PASSED") << std::endl;
  return failures ? 1 : 0;
}
