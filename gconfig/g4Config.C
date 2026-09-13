// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
#include "G4UImanager.hh"

// Configuration macro for Geant4 VirtualMC
void Config() {
  ///    Create the run configuration
  /// In constructor user has to specify the geometry input
  /// and select geometry navigation via the following options:
  /// - geomVMCtoGeant4   - geometry defined via VMC, G4 native navigation
  /// - geomVMCtoRoot     - geometry defined via VMC, Root navigation
  /// - geomRoot          - geometry defined via Root, Root navigation
  /// - geomRootToGeant4  - geometry defined via Root, G4 native navigation
  /// - geomGeant4        - geometry defined via Geant4, G4 native navigation
  ///
  /// The second argument in the constructor selects physics list:
  /// - emStandard         - standard em physics (default)
  /// - emStandard+optical - standard em physics + optical physics
  /// - XYZ                - selected hadron physics list ( XYZ = LHEP, QGSP,
  /// ...)
  /// - XYZ+optical        - selected hadron physics list + optical physics
  ///
  /// The third argument activates the special processes in the
  /// TG4SpecialPhysicsList, which implement VMC features:
  /// - stepLimiter       - step limiter (default)
  /// - specialCuts       - VMC cuts
  /// - specialControls   - VMC controls for activation/inactivation selected
  /// processes
  /// - stackPopper       - stackPopper process
  /// When more than one options are selected, they should be separated with '+'
  /// character: eg. stepLimit+specialCuts.

  const char* env = std::getenv("KAON_PION_SPLITS");
  int32_t fNsplits = env ? std::atoi(env) : 0;

  std::string controls = "stepLimiter+specialCuts+specialControls";
  /// stackPopper is required when adding secondaries, e.g. when splitting the
  /// pions and kaons
  if (fNsplits > 0) controls += "+stackPopper";
  TG4RunConfiguration* runConfiguration =
      new TG4RunConfiguration("geomRoot", "FTFP_BERT_HP_EMZ", controls.c_str(),
                              false,   // specialStacking (default)
                              false);  // disable MT

  /// Create the G4 VMC
  TGeant4* geant4 =
      new TGeant4("TGeant4", "The Geant4 Monte Carlo", runConfiguration);
  /// create the Specific stack
  ShipStack* stack = new ShipStack(1000);
  stack->StoreSecondaries(kTRUE);
  stack->SetMinPoints(0);
  geant4->SetStack(stack);
  // if(FairRunSim::Instance()->IsExtDecayer()){
  //    // does not work ! TVirtualMCDecayer* decayer =
  //    TPythia8Decayer::Instance();
  //   TVirtualMCDecayer* decayer = TVirtualMCDecayer* TPythia8Decayer();
  //   geant4->SetExternalDecayer(decayer);
  // }

  /// Customise Geant4 setting
  /// (verbose level, global range cut, ..)

  TString configm(gSystem->Getenv("VMCWORKDIR"));
  TString configm1 = configm + "/gconfig/g4config.in";
  std::cout << " -I g4Config() using g4conf  macro: " << configm1 << std::endl;
  // set geant4 specific stuff
  // still stupid bug in geant4_vmc
  // geant4->SetMaxNStep(10000.);  // default is 30000
  geant4->ProcessGeantMacro(configm1.Data());

  const std::string set_general_process_to_false =
      getenv("SET_GENERAL_PROCESS_TO_FALSE")
          ? getenv("SET_GENERAL_PROCESS_TO_FALSE")
          : "";
  if (set_general_process_to_false == "1") {
    // Turn off UseGeneralProcess to access GammaToMuons directly when
    // cross-sections need to be changed
    std::cout << "Setting /process/em/UseGeneralProcess false" << std::endl;
    G4UImanager::GetUIpointer()->ApplyCommand(
        "/process/em/UseGeneralProcess false");
  }

  const std::string use_heavy_decayer = getenv("EXTDECAYER_HEAVY_HADRONS")
                                            ? getenv("EXTDECAYER_HEAVY_HADRONS")
                                            : "";

  if (use_heavy_decayer == "1") {
    std::cout << "Configuring external decayer selection for heavy hadrons"
              << std::endl;

    // clang-format off
    std::vector<int> heavyHadronsPDG = {
      // charm mesons
      411, -411, 421, -421, 431, -431, 413, -413, 423, -423, 433, -433,
      // beauty mesons
      511, -511, 521, -521, 531, -531, 541, -541, 513, -513, 523, -523, 533, -533,
      // ccbar and bbbar
      443, 553, 10441, 20443, 445, 10551, 20553, 555,
      // charm baryons
      4122, -4122, 4222, -4222, 4212, -4212, 4112, -4112, 4232, -4232, 4132, -4132, 4332, -4332,
      // beauty baryons
      5122, -5122, 5112, -5112, 5212, -5212, 5222, -5222, 5132, -5132, 5232, -5232, 5332, -5332,
      // taus
      15, -15
    };
    // clang-format on

    const char* evtgendata = gSystem->Getenv("EVTGENDATA");
    if (!evtgendata || *evtgendata == '\0') {
      LOG(fatal) << "EVTGENDATA environment variable not set";
    }
    TEvtGenDecayer* decayer = new TEvtGenDecayer();
    decayer->SetEvtGenDecayFile(
        (std::string(evtgendata) + "/DECAY.DEC").c_str());
    decayer->SetEvtGenParticleFile(
        (std::string(evtgendata) + "/evt.pdl").c_str());

    std::string heavyHadronsString = "";
    for (int pdg : heavyHadronsPDG) {
      decayer->AddEvtGenParticle(pdg);
      TParticlePDG* p = TDatabasePDG::Instance()->GetParticle(pdg);
      if (p) heavyHadronsString += std::string(p->GetName()) + " ";
    }

    decayer->Init();
    geant4->SetExternalDecayer(decayer);
    G4UImanager::GetUIpointer()->ApplyCommand(
        "/mcPhysics/setExtDecayerSelection " + heavyHadronsString);
  }
}
