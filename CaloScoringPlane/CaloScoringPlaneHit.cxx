// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "CaloScoringPlaneHit.h"

#include <iostream>

#include "CaloScoringPlanePoint.h"
#include "FairLogger.h"
#include "TRandom.h"

CaloScoringPlaneHit::CaloScoringPlaneHit() : SHiP::DetectorHit() {}

CaloScoringPlaneHit::CaloScoringPlaneHit(const CaloScoringPlanePoint* p,
                                         Double_t t0, Double_t pos_res,
                                         Double_t time_res, Int_t pid)
    : SHiP::DetectorHit() {
  if (!p) {
    LOG(error) << "CaloScoringPlaneHit: null CaloScoringPlanePoint pointer";
    return;
  }
  fDetectorID = p->GetDetectorID();
  fX = pos_res > 0. ? gRandom->Gaus(p->GetX(), pos_res) : p->GetX();
  fY = pos_res > 0. ? gRandom->Gaus(p->GetY(), pos_res) : p->GetY();
  fZ = p->GetZ();
  const Double_t t = p->GetTime() + t0;
  fTime = time_res > 0. ? gRandom->Gaus(t, time_res) : t;
  fPx = p->GetPx();
  fPy = p->GetPy();
  fPz = p->GetPz();
  fPid = pid;
}

void CaloScoringPlaneHit::Print() const {
  std::cout << "-I- CaloScoringPlaneHit: detector " << fDetectorID << std::endl;
  std::cout << "    Position: (" << fX << ", " << fY << ", " << fZ << ") cm"
            << "  time " << fTime << " ns" << std::endl;
  std::cout << "    Momentum: (" << fPx << ", " << fPy << ", " << fPz
            << ") GeV/c  PID " << CaloScoringPlanePID::SpeciesName(fPid)
            << std::endl;
}
