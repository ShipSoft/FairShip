// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef PASSIVE_SHIPCAVE_H_
#define PASSIVE_SHIPCAVE_H_

#include "FairModule.h"  // for FairModule
#include "Rtypes.h"      // for ShipCave::Class, ClassDef, etc

class ShipCave : public FairModule {
 public:
  explicit ShipCave(Double_t z);
  explicit ShipCave(const char* name, const char* Title = "Exp Cave");
  ShipCave();
  ~ShipCave() override;
  void ConstructGeometry() override;

 private:
  Double_t z_end_of_proximity_shielding;
  Double_t world[3];

 public:
};

#endif  // PASSIVE_SHIPCAVE_H_
