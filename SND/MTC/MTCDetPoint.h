// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SND_MTC_MTCDETPOINT_H_
#define SND_MTC_MTCDETPOINT_H_

#include "DetectorPoint.h"
#include "TVector3.h"

class MTCDetPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  MTCDetPoint() = default;

  /** Constructor with arguments
   *@param trackID  Index of MCTrack
   *@param detID    Detector ID
   *@param pos      Coordinates at entrance to active volume [cm]
   *@param mom      Momentum of track at entrance [GeV]
   *@param tof      Time since event start [ns]
   *@param length   Track length since creation [cm]
   *@param eLoss    Energy deposit [GeV]
   *@param pdgCode  PDG code of the track
   **/
  MTCDetPoint(Int_t trackID, Int_t detID, const TVector3& pos,
              const TVector3& mom, Double_t tof, Double_t length,
              Double_t eLoss, Int_t pdgCode)
      : SHiP::DetectorPoint(0, trackID, detID, pos, mom, tof, length, eLoss,
                            pdgCode) {}

  Int_t GetLayer() const {
    return static_cast<int>(fDetectorID / 1000000) % 100;
  }
  Int_t GetLayerType() const {
    return static_cast<int>(fDetectorID / 100000) % 10;
  }

  ClassDefOverride(MTCDetPoint, 4)
};

#endif  // SND_MTC_MTCDETPOINT_H_
