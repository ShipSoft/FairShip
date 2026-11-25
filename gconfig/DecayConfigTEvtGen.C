// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

void DecayConfig() {
  // External decayer for the transport: EvtGen decays J/psi and Upsilon(1S),
  // Pythia8 the other particles Geant4 hands over (tau, charm and bottom
  // hadrons). Products with c tau0 above 1 um go back to Geant4 undecayed.

  // Create the custom EvtGen decayer
  TEvtGenDecayer* decayer = new TEvtGenDecayer();

  // Configure EvtGen files using EVTGENDATA
  TString DecayFile = TString(gSystem->Getenv("EVTGENDATA")) + "/DECAY.DEC";
  TString ParticleFile = TString(gSystem->Getenv("EVTGENDATA")) + "/evt.pdl";

  decayer->SetEvtGenDecayFile(DecayFile.Data());
  decayer->SetEvtGenParticleFile(ParticleFile.Data());

  // Configure which particles should use EvtGen
  decayer->AddEvtGenParticle(443);  // J/psi
  decayer->AddEvtGenParticle(553);  // Upsilon(1S)

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

  cout << "=== TEvtGenDecayer Configuration ===" << endl;
  cout << "EvtGen decay file: " << DecayFile << endl;
  cout << "EvtGen particle file: " << ParticleFile << endl;
  cout << "Particles using EvtGen: J/psi(443), Upsilon(553)" << endl;
  cout << "Other particles are decayed by Pythia8" << endl;
}
