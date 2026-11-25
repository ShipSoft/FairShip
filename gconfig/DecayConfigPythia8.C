// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

void DecayConfig() {
  // External decayer for the transport without EvtGen: Pythia8 decays every
  // particle Geant4 hands over (tau, charm and bottom hadrons, J/psi).
  // Products with c tau0 above 1 um go back to Geant4 undecayed.
  // For runs whose generator sets up EvtGen itself (FixedTargetGenerator):
  // EvtGen, through TAUOLA, can be set up only once per process.

  TEvtGenDecayer* decayer = new TEvtGenDecayer();
  decayer->Init();

  // Tell the concrete monte carlo to use the external decayer
  gMC->SetExternalDecayer(decayer);

  // Geant4 uses the external decayer for particles without a decay table.
  // Remove Geant4's decay table of tau here. Charm and bottom hadrons,
  // J/psi and Upsilon(1S) get their Geant4 decay tables only later, while
  // the physics is built, so python/external_decays.py removes those after
  // run.Init().
  gMC->SetUserDecay(15);   // tau-
  gMC->SetUserDecay(-15);  // tau+

  cout << "=== TEvtGenDecayer Configuration: Pythia8 only ===" << endl;
}
