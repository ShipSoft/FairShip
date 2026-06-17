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
  ClassDefOverride(ShipTargetStation, 6);

 protected:
  Double_t fTargetLength;       //
  Double_t fTargetZ;            //
  Double_t fDiameter;           //
  std::vector<float> fL;        // absorber width per layer
  std::vector<float> fG;        // gap after layer
  std::vector<std::string> fM;  // absorber material
  size_t fnS;
  Int_t fHeT;
};
#endif  // PASSIVE_SHIPTARGETSTATION_H_
