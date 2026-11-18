// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef MUONSHIELDOPTIMIZATION_PYFAIRMODULE_H_
#define MUONSHIELDOPTIMIZATION_PYFAIRMODULE_H_

struct _object;
typedef _object PyObject;
#include <stdexcept>
#include <string>
#include <vector>

#include "FairModule.h"
void call_python_method(PyObject* self, const char* method);

class pyFairModule : public FairModule {
 public:
  explicit pyFairModule(PyObject* self) : fSelf(self) {}
  ~pyFairModule() override = default;
  void ConstructGeometry() override {
    call_python_method(fSelf, "ConstructGeometry");
  }
  /// Names of the volumes that the modules of this run registered as
  /// sensitive so far, as FairDetector::Initialize() looks them up in the
  /// geometry given to Geant4 (without a "#" copy suffix). Compiled, because
  /// the list is thread_local, which the interpreter cannot reach reliably.
  /// With a module name, only the volumes that module registered.
  static std::vector<std::string> SensitiveVolumeNames(
      const std::string& module = "");

 private:
  PyObject* fSelf;
};

#endif  // MUONSHIELDOPTIMIZATION_PYFAIRMODULE_H_
