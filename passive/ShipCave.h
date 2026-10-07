// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef PASSIVE_SHIPCAVE_H_
#define PASSIVE_SHIPCAVE_H_

#include "FairModule.h"  // for FairModule
#include "Rtypes.h"      // for ShipCave::Class, ClassDef, etc

class ShipCave : public FairModule {
 public:
  ShipCave(Double_t z_end_of_proximity_shielding, Double_t z_transition,
           Double_t z_spectrometer);
  explicit ShipCave(const char* name, const char* Title = "Exp Cave");
  ShipCave();
  ~ShipCave() override;
  void ConstructGeometry() override;

 private:
  Double_t z_end_of_proximity_shielding;
  Double_t fZTransition;    // TCC8/ECN3 step
  Double_t fZSpectrometer;  // mid-plane of the spectrometer magnet (yoke pit)
  Double_t world[3];

 public:
};

#endif  // PASSIVE_SHIPCAVE_H_
