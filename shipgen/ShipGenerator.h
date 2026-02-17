// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_SHIPGENERATOR_H_
#define SHIPGEN_SHIPGENERATOR_H_ 1

#include <iostream>
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

namespace Ship {
class Generator : public FairGenerator {
 public:
  Generator() {};
  virtual ~Generator();

  virtual Bool_t Init(const char*, int) = 0;
  virtual Bool_t Init(const char*) = 0;
  virtual Bool_t Init(const std::vector<std::string>& inFiles,
                      int startNumber) {
    std::cout << "WARNING: Multiple input files not implemented for this "
                 "generator - only taking the first!"
              << std::endl;
    return Init(inFiles.at(0).c_str(), startNumber);
  };
  virtual Bool_t Init(const std::vector<std::string>& inFiles) {
    std::cout << "WARNING: Multiple input files not implemented for this "
                 "generator - only taking the first!"
              << std::endl;
    return Init(inFiles.at(0).c_str(), 0);
  };

  virtual void UseExternalFile(const char* x, Int_t i) {
    fextFile = x;
    firstEvent = i;
  };

  virtual void UseExternalFile(std::vector<std::string>& inFiles, Int_t i) {
    std::cout << "WARNING: Multiple external files not implemented for this "
                 "generator - only taking the first!"
              << std::endl;
    UseExternalFile(inFiles.at(0).c_str(), i);
  }

 protected:
  const char* fextFile = nullptr;
  Int_t firstEvent = 0;
  ClassDef(Ship::Generator, 1);
};
}  // namespace Ship
#endif  // SHIPGEN_SHIPGENERATOR_H_
