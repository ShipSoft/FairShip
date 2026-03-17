// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "strawtubesHit.h"

#include <cmath>
#include <iostream>
#include <tuple>

#include "FairLogger.h"
#include "FairRun.h"
#include "FairRunSim.h"
#include "TGeoManager.h"
#include "TGeoShape.h"
#include "TGeoTube.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TVector3.h"
#include "strawtubes.h"
using std::cout;
using std::endl;

namespace {
constexpr Double_t speedOfLight = 29.9792458;  // TMath::C() * 100 / 1e9, cm/ns
}  // namespace
// -----   Default constructor   -------------------------------------------
strawtubesHit::strawtubesHit() : SHiP::DetectorHit() {}
// -----   Standard constructor   ------------------------------------------
strawtubesHit::strawtubesHit(Int_t detID, Float_t tdc)
    : SHiP::DetectorHit(detID, tdc) {}
// -----   constructor from strawtubesPoint
// ------------------------------------------
strawtubesHit::strawtubesHit(strawtubesPoint* p, Double_t t0)
    : SHiP::DetectorHit() {
  if (!p) {
    LOG(error) << "strawtubesHit: null strawtubesPoint pointer";
    return;
  }
  TVector3 start = TVector3();
  TVector3 stop = TVector3();
  fDetectorID = p->GetDetectorID();
  strawtubes* module = dynamic_cast<strawtubes*>(
      FairRunSim::Instance()->GetListOfModules()->FindObject("strawtubes"));
  Double_t v_drift = module->StrawVdrift();
  Double_t sigma_spatial = module->StrawSigmaSpatial();
  strawtubes::StrawEndPoints(fDetectorID, start, stop);
  Double_t t_drift =
      fabs(gRandom->Gaus(p->dist2Wire(), sigma_spatial)) / v_drift;
  fdigi = t0 + p->GetTime() + t_drift + (stop[0] - p->GetX()) / speedOfLight;
}

// -------------------------------------------------------------------------

// -------------------------------------------------------------------------

Int_t strawtubesHit::GetStationNumber() const {
  Int_t detID = GetDetectorID();
  const auto decode = strawtubes::StrawDecode(detID);

  return std::get<0>(decode);
}

Int_t strawtubesHit::GetViewNumber() const {
  Int_t detID = GetDetectorID();
  const auto decode = strawtubes::StrawDecode(detID);

  return std::get<1>(decode);
}

Int_t strawtubesHit::GetLayerNumber() const {
  Int_t detID = GetDetectorID();
  const auto decode = strawtubes::StrawDecode(detID);

  return std::get<2>(decode);
}

Int_t strawtubesHit::GetStrawNumber() const {
  Int_t detID = GetDetectorID();
  const auto decode = strawtubes::StrawDecode(detID);

  return std::get<3>(decode);
}

// -----   Public method Print   -------------------------------------------
void strawtubesHit::Print() const {
  cout << "-I- strawtubesHit: strawtubes hit " << " in detector " << fDetectorID
       << endl;
  cout << "  TDC " << fdigi << " ns" << endl;
}
// -------------------------------------------------------------------------
