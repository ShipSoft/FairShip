// -------------------------------------------------------------------------
// -----                SHiP::VMCConfig source file                   -----
// -------------------------------------------------------------------------

#include "VMCConfig.h"

#include <cstdlib>
#include <iostream>
#include <memory>

#include "FairLogger.h"
#include "FairRunSim.h"
#include "ShipStack.h"
#include "TROOT.h"
#include "TVirtualMC.h"

namespace SHiP {

// -----   Constructor   ---------------------------------------------------
VMCConfig::VMCConfig(const std::string& name, const std::string& yamlFile)
    : FairYamlVMCConfig(), fYamlFile(yamlFile) {
  LOG(info) << "SHiP::VMCConfig: Constructor called with YAML file: "
            << fYamlFile;
}

// -----   Destructor   ----------------------------------------------------
VMCConfig::~VMCConfig() {}

// -----   Setup method   --------------------------------------------------
void VMCConfig::Setup(const char* mcEngine) {
  LOG(info) << "SHiP::VMCConfig: Setting up VMC for engine: " << mcEngine;

  // Call parent Setup method to handle YAML configuration loading
  // FairYamlVMCConfig will automatically find the YAML file based on mcEngine
  FairYamlVMCConfig::Setup(mcEngine);

  // Check if UseGeneralProcess should be disabled (needed to modify
  // GammaToMuons cross-sections directly for boost factor studies)
  const char* env = std::getenv("SET_GENERAL_PROCESS_TO_FALSE");
  if (env && std::string(env) == "1") {
    LOG(info) << "SHiP::VMCConfig: Setting /process/em/UseGeneralProcess false";
    gROOT->ProcessLine(
        "G4UImanager::GetUIpointer()->ApplyCommand("
        "\"/process/em/UseGeneralProcess false\")");
  }

  LOG(info) << "SHiP::VMCConfig: Setup completed successfully";
}

// -----   SetupStack method (pure virtual from base class)   -----------------
void VMCConfig::SetupStack() {
  LOG(info) << "SHiP::VMCConfig: Setting up stack";

  // Create and configure ShipStack for SHiP-specific functionality
  CreateShipStack();
}

// -----   Private method to create ShipStack   ---------------------------
void VMCConfig::CreateShipStack() {
  LOG(info) << "SHiP::VMCConfig: Creating and configuring ShipStack";

  // Create ShipStack with default size of 1000
  ShipStack* stack = new ShipStack(1000);

  // Configure stack settings
  stack->StoreSecondaries(kTRUE);
  stack->SetMinPoints(0);

  // Set the stack to the VMC engine
  TVirtualMC* mc = TVirtualMC::GetMC();
  if (mc) {
    mc->SetStack(stack);
    LOG(info) << "SHiP::VMCConfig: ShipStack successfully set to VMC engine";
  } else {
    LOG(error) << "SHiP::VMCConfig: Could not get VMC instance to set stack";
  }
}

// -----   Free helper function   ------------------------------------------
void SetupVMCConfig(const char* name, const char* yamlFile) {
  auto config = std::make_unique<VMCConfig>(name, yamlFile);
  FairRunSim::Instance()->SetSimulationConfig(std::move(config));
}

}  // namespace SHiP
