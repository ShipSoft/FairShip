// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "pyFairModule.h"

#include "FairVolume.h"
#include "Python.h"  // Needs to be included first to avoid redefinition of _POSIX_C_SOURCE
#include "TObject.h"

std::vector<std::string> pyFairModule::SensitiveVolumeNames() {
  std::vector<std::string> names;
  names.reserve(fAllSensitiveVolumes.size());
  for (const FairVolume* volume : fAllSensitiveVolumes) {
    if (!volume) {
      continue;
    }
    std::string name = volume->GetName();
    // Same cut as in FairDetector::Initialize()
    const auto pos = name.find('#', 1);
    if (pos != std::string::npos && pos > 1) {
      name.resize(pos);
    }
    names.push_back(name);
  }
  return names;
}

void call_python_method(PyObject* self, const char* method) {
  // check arguments
  if (nullptr == self || nullptr == method) {
    throw std::runtime_error("Invalid Python object and method");
  }
  // call Python
  PyObject* r = PyObject_CallMethod(self, const_cast<char*>(method),
                                    const_cast<char*>(""));
  if (nullptr == r) {
    PyErr_Print();
    return;
  }
  // release used objects
  Py_XDECREF(r);
  //
  return;
}
