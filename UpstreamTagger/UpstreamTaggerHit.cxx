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
    : SHiP::DetectorHit(),
      fX(0.),
      fY(0.),
      fZ(0.),
      fTime(0.),
      fTileID(-1),
      fTriggered(kFALSE) {}

// -----   Constructor from UpstreamTaggerPoint   --------------
UpstreamTaggerHit::UpstreamTaggerHit(UpstreamTaggerPoint* p, Double_t t0,
                                     const TVector3& digitizedPosition,
                                     Double_t time_res)
    : SHiP::DetectorHit(), fTileID(-1), fTriggered(kFALSE) {
  if (!p) {
    LOG(error) << "UpstreamTaggerHit: null UpstreamTaggerPoint pointer";
    return;
  }
  fDetectorID = p->GetDetectorID();
  fX = digitizedPosition.X();
  fY = digitizedPosition.Y();
  fZ = digitizedPosition.Z();
  fTime = gRandom->Gaus(p->GetTime() + t0, time_res);
}

// -----   Print   ------------------------------
void UpstreamTaggerHit::Print() const {
  cout << "-I- UpstreamTaggerHit: detector " << fDetectorID << endl;
  cout << "    Constituent tile ID: " << fTileID << endl;
  cout << "    Position: (" << fX << ", " << fY << ", " << fZ << ") cm" << endl;
  cout << "    Time: " << fTime << " ns" << endl;
  cout << "    ADC: " << GetADC()
       << ", triggered: " << (fTriggered ? "yes" : "no") << endl;
}
