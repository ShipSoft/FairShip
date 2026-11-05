// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef PASSIVE_SHIPMUONSHIELD_H_
#define PASSIVE_SHIPMUONSHIELD_H_

#include <map>
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
// and half height. n_magnets is the expected number of magnets, so that a
// parameter list in another format (e.g. from an older geometry file) fails.
class ShipMuonShield : public FairModule {
 public:
  ShipMuonShield(std::vector<double> in_params, size_t n_magnets, Double_t z);
  ShipMuonShield();
  ~ShipMuonShield() override;
  void ConstructGeometry() override;
  // Cut a hole of half width hole_dx and half height hole_dy for the SND
  // through the centre of magnets first_magnet..last_magnet (0-based).
  void SetSNDSpace(Bool_t hole, Double_t hole_dx, Double_t hole_dy,
                   Int_t first_magnet, Int_t last_magnet);
  // Fill the space between the cavern floor and magnets first_magnet..last
  // (0-based) with concrete blocks of the magnet width and length, floor_gap
  // above the floor and magnet_gap below the magnet. The floor steps down
  // from TCC8 to the stair step at z_transition and to ECN3 after
  // stair_step_length; a block over a step is split there.
  void SetFloorBlocks(Int_t first_magnet, Double_t floor_gap,
                      Double_t magnet_gap, Double_t z_transition,
                      Double_t stair_step_length);
  // No floor block over the stair step (TCC8 -> ECN3) for this magnet.
  void SkipFloorBlockOnStair(Int_t magnet);
  // Gap between the cavern floor and the floor blocks of this magnet,
  // instead of the common floor_gap (e.g. room for electronics, left as air).
  void SetFloorBlockFloorGap(Int_t magnet, Double_t floor_gap);

  static constexpr size_t nParams = 4;

 protected:
  Double_t z_end_of_proximity_shielding{0.};
  size_t nMagnets{0};
  std::vector<Double_t> shield_params;
  Bool_t snd_hole{false};
  Double_t snd_hole_dx = 0., snd_hole_dy = 0.;
  Int_t snd_first_magnet{-1}, snd_last_magnet{-1};
  Int_t floor_blocks_first_magnet{-1};  // -1: no floor blocks
  Double_t floor_blocks_floor_gap{0.}, floor_blocks_magnet_gap{0.};
  Double_t cave_z_transition{0.}, cave_stair_step_length{0.};
  std::vector<Int_t> floor_blocks_no_stair;
  std::map<Int_t, Double_t> floor_blocks_floor_gap_per_magnet;

  void CreateMagnet(const TString& magnetName, TGeoMedium* medium,
                    TGeoVolume* tShield, Double_t dX, Double_t dY, Double_t dZ,
                    Double_t Z, Bool_t withSNDHole);
  void CreateFloorBlocks(Int_t magnet, const TString& magnetName,
                         TGeoMedium* medium, TGeoVolume* tShield, Double_t dX,
                         Double_t dY, Double_t dZ, Double_t Z);
};

#endif  // PASSIVE_SHIPMUONSHIELD_H_
