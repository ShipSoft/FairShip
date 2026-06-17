// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef MUONSHIELDOPTIMIZATION_PYFAIRMODULE_H_
#define MUONSHIELDOPTIMIZATION_PYFAIRMODULE_H_

struct _object;
typedef _object PyObject;
#include <stdexcept>

#include "FairModule.h"
void call_python_method(PyObject* self, const char* method);

class pyFairModule : public FairModule {
 public:
  explicit pyFairModule(PyObject* self) : fSelf(self) {}
  ~pyFairModule() override = default;
  void ConstructGeometry() override {
    call_python_method(fSelf, "ConstructGeometry");
  }

 private:
  PyObject* fSelf;
};

#endif  // MUONSHIELDOPTIMIZATION_PYFAIRMODULE_H_
