// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "Detector.h"

#include "DetectorPoint.h"
#include "FairLogger.h"
#include "FairRootManager.h"

SHiP::Detector::Detector(const char* Name, Bool_t Active, Int_t detID)
    : FairDetector(Name, Active, detID),
      fEventID(-1),
      fTrackID(-1),
      fVolumeID(-1),
      fPos(),
      fMom(),
      fTime(-1.),
      fLength(-1.),
      fELoss(-1),
      fDetPoints(NULL) {}

SHiP::Detector::Detector(const char* Name, Bool_t Active)
    : Detector(Name, Active, 0) {}

SHiP::Detector::~SHiP::Detector() {
  if (fDetPoints) {
    fDetPoints->clear();
    delete fDetPoints;
  }
}

void SHiP::Detector::Initialize() { FairDetector::Initialize(); }

void SHiP::Detector::Reset() { fDetPoints->clear(); }

SHiP::DetectorPoint* SHiP::Detector::AddHit(Int_t eventID, Int_t trackID,
                                            Int_t detID, const TVector3& pos,
                                            const TVector3& mom, Double_t time,
                                            Double_t length, Double_t eLoss,
                                            Int_t pdgCode, const TVector3& Lpos,
                                            const TVector3& Lmom) {
  fDetPoints->emplace_back(eventID, trackID, detID, pos, mom, time, length,
                           eLoss, pdgCode, Lpos, Lmom);
  return &(fDetPoints->back());
}

void SHiP::Detector::EndOfEvent() { fDetPoints->clear(); }
