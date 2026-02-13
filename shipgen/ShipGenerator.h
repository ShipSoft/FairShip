// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_SHIPGENERATOR_H_
#define SHIPGEN_SHIPGENERATOR_H_ 1

#include <string>
#include <vector>

#include "FairGenerator.h"
#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "TChain.h"      // for TChain
#include "TClonesArray.h"
#include "TROOT.h"

class FairPrimaryGenerator;
class ShipMCTrack;
class vetoPoint;

class ShipGenerator : public FairGenerator {
 public:
  ShipGenerator() {};
  virtual ~ShipGenerator();

  virtual Bool_t Init(const char*, int) = 0;
  virtual Bool_t Init(const char*) = 0;
  virtual Bool_t Init(const std::vector<std::string>& inFiles,
                      int startNumber) {
    return Init(inFiles.at(0).c_str(), startNumber);
  };
  virtual Bool_t Init(const std::vector<std::string>& inFiles) {
    return Init(inFiles.at(0).c_str(), 0);
  };

 protected:
  ClassDef(ShipGenerator, 1);
};

#endif  // SHIPGEN_SHIPGENERATOR_H_
