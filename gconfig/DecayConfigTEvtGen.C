// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

void DecayConfig() {
  // This script uses TEvtGenDecayer that handles J/psi with EvtGen
  // and other particles with TPythia8Decayer

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

  // Configure particles to use external decayer
  gMC->SetUserDecay(411);    // D+
  gMC->SetUserDecay(-411);   // D-
  gMC->SetUserDecay(421);    // D0
  gMC->SetUserDecay(-421);   // anti-D0
  gMC->SetUserDecay(4122);   // Lambda_c+
  gMC->SetUserDecay(-4122);  // Lambda_c-
  gMC->SetUserDecay(431);    // D_s+
  gMC->SetUserDecay(-431);   // D_s-
  gMC->SetUserDecay(15);     // tau+
  gMC->SetUserDecay(-15);    // tau-

  // Configure charmonium and bottomonium to use external decayer (EvtGen)
  gMC->SetUserDecay(443);  // J/psi
  gMC->SetUserDecay(553);  // Upsilon(1S)

  cout << "=== TEvtGenDecayer Configuration ===" << endl;
  cout << "EvtGen decay file: " << DecayFile << endl;
  cout << "EvtGen particle file: " << ParticleFile << endl;
  cout << "Particles using EvtGen: J/psi(443), Upsilon(553)" << endl;
  cout << "Other particles use TPythia8Decayer fallback" << endl;
}
