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

  /** Cavern dimensions (cm); defaults match the ECN3 layout. */
  void SetCavernDimensions(Double_t TCC8_length, Double_t ECN3_length,
                           Double_t stair_step_length, Double_t z_transition) {
    fTCC8Length = TCC8_length;
    fECN3Length = ECN3_length;
    fStairStepLength = stair_step_length;
    fZTransition = z_transition;
  }
  /** z of the downstream ECN3 wall (cm). */
  Double_t GetCavernEndZ() const { return fZTransition + fECN3Length; }

 private:
  Double_t fTCC8Length = 17000.;
  Double_t fECN3Length = 10000.;
  Double_t fStairStepLength = 82.;
  Double_t fZTransition = 2052.;
  Double_t z_end_of_proximity_shielding;
  Double_t world[3];

 public:
};

#endif  // PASSIVE_SHIPCAVE_H_
