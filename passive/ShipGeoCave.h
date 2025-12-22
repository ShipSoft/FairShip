// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef PASSIVE_SHIPGEOCAVE_H_
#define PASSIVE_SHIPGEOCAVE_H_

#include <fstream>  // for fstream
#include <iosfwd>   // for fstream

#include "FairGeoSet.h"  // for FairGeoSet
#include "Rtypes.h"      // for ShipGeoCave::Class, Bool_t, etc
#include "TString.h"     // for TString

class FairGeoMedia;

class ShipGeoCave : public FairGeoSet {
 protected:
  TString name;

 public:
  ShipGeoCave();
  ~ShipGeoCave() {}
  const char* getModuleName(Int_t) { return name.Data(); }
  Bool_t read(std::fstream&, FairGeoMedia*);
  void addRefNodes();
  void write(std::fstream&);
  void print();
  ClassDef(ShipGeoCave, 0)  // Class for the geometry of CAVE
};

#endif  // PASSIVE_SHIPGEOCAVE_H_  /* !PNDGEOCAVE_H */
