// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTaggerHit.h"

#include <iostream>

#include "FairLogger.h"
#include "TRandom.h"
#include "UpstreamTaggerPoint.h"

using std::cout;
using std::endl;

// -----   Default constructor   --------------
UpstreamTaggerHit::UpstreamTaggerHit()
    : SHiP::DetectorHit(), fX(0.), fY(0.), fZ(0.), fTime(0.) {}

// -----   Constructor from UpstreamTaggerPoint   --------------
UpstreamTaggerHit::UpstreamTaggerHit(UpstreamTaggerPoint* p, Double_t t0,
                                     Double_t pos_res, Double_t time_res)
    : SHiP::DetectorHit() {
  if (!p) {
    LOG(error) << "UpstreamTaggerHit: null UpstreamTaggerPoint pointer";
    return;
  }
  fDetectorID = p->GetDetectorID();

  // Smear position with Gaussian resolution
  fX = gRandom->Gaus(p->GetX(), pos_res);
  fY = gRandom->Gaus(p->GetY(), pos_res);
  fZ = gRandom->Gaus(p->GetZ(), pos_res);

  // Smear time with Gaussian resolution
  fTime = gRandom->Gaus(p->GetTime() + t0, time_res);

  //  fSubDetID = p->GetLayerID();
}

// -----   Print   ------------------------------
void UpstreamTaggerHit::Print() const {
  cout << "-I- UpstreamTaggerHit: detector " << fDetectorID << endl;
  cout << "    Position: (" << fX << ", " << fY << ", " << fZ << ") cm" << endl;
  cout << "    Time: " << fTime << " ns" << endl;
}
