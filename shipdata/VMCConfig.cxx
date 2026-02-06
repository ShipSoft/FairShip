// -------------------------------------------------------------------------
// -----                SHiP::VMCConfig source file                   -----
// -------------------------------------------------------------------------

#include "VMCConfig.h"

#include <iostream>

#include "FairLogger.h"
#include "ShipStack.h"
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

}  // namespace SHiP
