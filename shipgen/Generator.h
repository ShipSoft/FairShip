// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_GENERATOR_H_
#define SHIPGEN_GENERATOR_H_ 1

#include <optional>
#include <string>
#include <vector>

#include "FairGenerator.h"
#include "FairLogger.h"

namespace SHiP {
class Generator : public FairGenerator {
 public:
  Generator() {};
  virtual ~Generator();

  virtual Bool_t Init(const char*, int) = 0;
  virtual Bool_t Init(const char*) = 0;
  virtual Bool_t Init(const std::vector<std::string>& inFiles,
                      int startNumber) {
    LOG(warning) << "Multiple input files not implemented for this generator "
                    "- only taking the first!";
    return Init(inFiles.at(0).c_str(), startNumber);
  };
  virtual Bool_t Init(const std::vector<std::string>& inFiles) {
    LOG(warning) << "Multiple input files not implemented for this generator "
                    "- only taking the first!";
    return Init(inFiles.at(0).c_str(), 0);
  };

  virtual void UseExternalFile(std::string x, Int_t i) {
    fextFile = x;
    firstEvent = i;
  };

  virtual void UseExternalFile(std::vector<std::string>& inFiles, Int_t i) {
    LOG(warning) << "Multiple external files not implemented for this "
                    "generator - only taking the first!";
    UseExternalFile(inFiles.at(0).c_str(), i);
  }

 protected:
  std::optional<std::string> fextFile;
  Int_t firstEvent = 0;
  ClassDef(SHiP::Generator, 2);
};
}  // namespace SHiP
#endif  // SHIPGEN_GENERATOR_H_
