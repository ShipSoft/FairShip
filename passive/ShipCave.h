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

  /** Sets the ECN3 experiment cavern: half width, half height, the x, y
   * position of its centre and the height of the stair step at its entrance,
   * where the floor is raised */
  void SetECN3Cavern(Double_t halfX, Double_t halfY, Double_t centerX,
                     Double_t centerY, Double_t stairStepHeight) {
    fECN3HalfX = halfX;
    fECN3HalfY = halfY;
    fECN3CenterX = centerX;
    fECN3CenterY = centerY;
    fECN3StairStepHeight = stairStepHeight;
  }

 private:
  Double_t z_end_of_proximity_shielding;
  Double_t fECN3HalfX = 799.5;          // ECN3 cavern half width (cm)
  Double_t fECN3HalfY = 600.;           // ECN3 cavern half height (cm)
  Double_t fECN3CenterX = 343.5;        // ECN3 cavern centre x (cm)
  Double_t fECN3CenterY = 264.;         // ECN3 cavern centre y (cm)
  Double_t fECN3StairStepHeight = 80.;  // ECN3 entrance stair step (cm)
  Double_t world[3];

 public:
};

#endif  // PASSIVE_SHIPCAVE_H_
