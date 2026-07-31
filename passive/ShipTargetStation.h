// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef PASSIVE_SHIPTARGETSTATION_H_
#define PASSIVE_SHIPTARGETSTATION_H_

#include <cstdlib>
#include <string>  // for string

#include "FairModule.h"  // for FairModule
#include "Rtypes.h"      // for ShipTargetStation::Class, Bool_t, etc

class ShipTargetStation : public FairModule {
 public:
  ShipTargetStation(const char* name, const Double_t tl, const Double_t tz,
                    const int nS, const int HeT,
                    const char* Title = "ShipTargetStation");
  ShipTargetStation();
  ~ShipTargetStation() override;
  void ConstructGeometry() override;
  void SetLayerPosMat(Float_t d, const std::vector<float>& L,
                      const std::vector<float>& G,
                      const std::vector<std::string>& M) {
    fDiameter = d;
    assert(L.size() == fnS);
    fL = L;
    assert(M.size() == fnS);
    fM = M;
    assert(G.size() == fnS);
    fG = G;
  }
  /** Target design version: 1 = legacy Ta-clad disks in steel enclosure,
      2 = 2026 BDF target (pure W disks, steel core with He grooves) */
  void SetDesign(Int_t design) { fDesign = design; }
  /** Diameter of the last (larger) disk, design 2 only */
  void SetLastDiskDiameter(Double_t d) { fDiameter2 = d; }
  /** Fixed reference length used to place the proximity shielding independently
      of the actual target length; set from the geometry config. */
  void SetShieldingReferenceLength(Double_t l) {
    fShieldingReferenceLength = l;
  }

 protected:
  Double_t fTargetLength;                 //
  Double_t fTargetZ;                      //
  Double_t fDiameter;                     //
  Double_t fDiameter2{0};                 // diameter of last disk (design 2)
  Double_t fShieldingReferenceLength{0};  // 0 = unset
  std::vector<float> fL;                  // absorber width per layer
  std::vector<float> fG;                  // gap after layer
  std::vector<std::string> fM;            // absorber material
  size_t fnS;
  Int_t fHeT;
  Int_t fDesign{1};
};
#endif  // PASSIVE_SHIPTARGETSTATION_H_
