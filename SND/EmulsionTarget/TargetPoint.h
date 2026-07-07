// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SND_EMULSIONTARGET_TARGETPOINT_H_
#define SND_EMULSIONTARGET_TARGETPOINT_H_

#include "DetectorPoint.h"
#include "TVector3.h"

class TargetPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  TargetPoint() = default;

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
  TargetPoint(Int_t trackID, Int_t detID, const TVector3& pos,
              const TVector3& mom, Double_t tof, Double_t length,
              Double_t eLoss, Int_t pdgCode)
      : SHiP::DetectorPoint(0, trackID, detID, pos, mom, tof, length, eLoss,
                            pdgCode) {}

  ClassDefOverride(TargetPoint, 4)
};

#endif  // SND_EMULSIONTARGET_TARGETPOINT_H_
