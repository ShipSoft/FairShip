// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef PASSIVE_SHIPMUONSHIELD_H_
#define PASSIVE_SHIPMUONSHIELD_H_

#include <vector>

#include "FairLogger.h"
#include "FairModule.h"  // for FairModule
#include "Rtypes.h"      // for ShipMuonShield::Class, Bool_t, etc
#include "TGeoMedium.h"
#include "TString.h"

// Muon shield made of one solid iron box per magnet. The magnetic field is
// not attached to the volumes: it comes from the field map
// files/<shieldName>.root (see geomGeant4.addVMCFields).
//
// in_params holds nParams values per magnet, all in cm:
//   [Zgap, dZ, dX, dY]
// Zgap: gap upstream of the magnet, dZ: half length, dX/dY: outer half width
// and half height.
class ShipMuonShield : public FairModule {
 public:
  ShipMuonShield(std::vector<double> in_params, Double_t z);
  ShipMuonShield();
  ~ShipMuonShield() override;
  void ConstructGeometry() override;
  // Cut a hole of half width hole_dx and half height hole_dy for the SND
  // through the centre of magnets first_magnet..last_magnet (0-based).
  void SetSNDSpace(Bool_t hole, Double_t hole_dx, Double_t hole_dy,
                   Int_t first_magnet, Int_t last_magnet);

  static constexpr size_t nParams = 4;

 protected:
  Double_t z_end_of_proximity_shielding{0.};
  size_t nMagnets{0};
  std::vector<Double_t> shield_params;
  Bool_t snd_hole{false};
  Double_t snd_hole_dx = 0., snd_hole_dy = 0.;
  Int_t snd_first_magnet{-1}, snd_last_magnet{-1};

  void CreateMagnet(const TString& magnetName, TGeoMedium* medium,
                    TGeoVolume* tShield, Double_t dX, Double_t dY, Double_t dZ,
                    Double_t Z, Bool_t withSNDHole);
};

#endif  // PASSIVE_SHIPMUONSHIELD_H_
