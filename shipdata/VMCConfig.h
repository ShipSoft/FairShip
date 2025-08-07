// -------------------------------------------------------------------------
// -----                  SHiP::VMCConfig header file                  -----
// -------------------------------------------------------------------------

/** VMCConfig.h
 **
 ** Custom VMC configuration class for SHiP experiment that inherits from
 ** FairYamlVMCConfig and provides SHiP-specific functionality including:
 ** - Automatic ShipStack instantiation and configuration
 ** - YAML configuration file loading from specified path
 ** - Integration with SHiP simulation framework
 **/

#ifndef SHIPDATA_VMCCONFIG_H_
#define SHIPDATA_VMCCONFIG_H_

#include <string>

#include "FairYamlVMCConfig.h"

class ShipStack;

namespace SHiP {

class VMCConfig : public FairYamlVMCConfig {
 public:
  /** Constructor with YAML file path
   *@param name       Configuration name (unused - kept for compatibility)
   *@param yamlFile   Path to YAML configuration file (unused - auto-discovered)
   **/
  explicit VMCConfig(const std::string& name = "g4Config",
                     const std::string& yamlFile = "g4Config.yaml");

  /** Destructor **/
  virtual ~VMCConfig();

  /** Setup VMC configuration
   *@param mcEngine  Monte Carlo engine name (e.g. "TGeant4")
   **/
  void Setup(const char* mcEngine) override;

 protected:
  /** Setup stack (pure virtual from FairYamlVMCConfig) **/
  void SetupStack() override;

 private:
  /** Create and configure ShipStack **/
  void CreateShipStack();

  /** YAML configuration file path **/
  std::string fYamlFile;
};

/** Helper to create and register a VMCConfig from compiled code. **/
void SetupVMCConfig(const char* name = "g4Config",
                    const char* yamlFile = "g4Config.yaml");

}  // namespace SHiP

#endif  // SHIPDATA_VMCCONFIG_H_
