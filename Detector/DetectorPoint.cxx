// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "DetectorPoint.h"

#include "FairLogger.h"

// -----   Standard constructor  ----------------
SHiP::DetectorPoint::DetectorPoint(Int_t eventID, Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom, Double_t tof,
                                   Double_t length, Double_t eLoss,
                                   Int_t pdgcode, TVector3 Lpos, TVector3 Lmom)
    : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss, eventID),
      fPdgCode(pdgcode),
      fLpos{Lpos.X(), Lpos.Y(), Lpos.Z()},
      fLmom{Lmom.X(), Lmom.Y(), Lmom.Z()} {}

// -----   Standard constructor  ----------------
SHiP::DetectorPoint::DetectorPoint(Int_t eventID, Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom, Double_t tof,
                                   Double_t length, Double_t eLoss,
                                   Int_t pdgcode)
    : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss, eventID),
      fPdgCode(pdgcode),
      fLpos{pos.X(), pos.Y(), pos.Z()},
      fLmom{mom.X(), mom.Y(), mom.Z()} {}

// -----   Public method Print   -------------------------------------------
void SHiP::DetectorPoint::Print() const {
  LOG(info) << "-I- " << ClassName() << " point for track " << fTrackID
            << " in detector " << fDetectorID;
  LOG(info) << "    Position (" << fX << ", " << fY << ", " << fZ << ") cm";
  LOG(info) << "    Momentum (" << fPx << ", " << fPy << ", " << fPz << ") GeV";
  LOG(info) << "    Time " << fTime << " ns,  Length " << fLength
            << " cm,  Energy loss " << fELoss * 1.0e06 << " keV";
  extraPrintInfo();
}
// -------------------------------------------------------------------------

void SHiP::DetectorPoint::extraPrintInfo() const {
  LOG(info) << "Nothing to see here";
}

ClassImp(SHiP::DetectorPoint)
