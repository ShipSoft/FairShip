// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SND_SIWCALO_SIWCALOPOINT_H_
#define SND_SIWCALO_SIWCALOPOINT_H_ 1
#include <cmath>

#include "DetectorPoint.h"
#include "TVector3.h"

class SiWCaloPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  SiWCaloPoint() = default;

  /** Constructor with arguments
   *@param trackID  Index of MCTrack
   *@param detID    Detector ID
   *@param pos      Ccoordinates at entrance to active volume [cm]
   *@param mom      Momentum of track at entrance [GeV]
   *@param tof      Time since event start [ns]
   *@param length   Track length since creation [cm]
   *@param eLoss    Energy deposit [GeV]
   *@param pdgcode  PDG code of MCTrack
   **/

  SiWCaloPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
               Double_t tof, Double_t length, Double_t eLoss, Int_t pdgcode)
      : SHiP::DetectorPoint(0, trackID, detID, pos, mom, tof, length, eLoss,
                            pdgcode) {}

  int constexpr GetLayer() { return fDetectorID >> 17; }
  int constexpr GetColumn() { return (fDetectorID >> 14) & 0x3; }
  int constexpr GetRow() { return (fDetectorID >> 13) & 0x1; }
  int constexpr GetPixelX() { return fDetectorID & 0x1F; }         // 0-31
  int constexpr GetPixelY() { return (fDetectorID >> 5) & 0x1F; }  // 0-31
  // Helpers
  int constexpr GetPixelID() {
    return GetPixelX() + 32 * GetPixelY();
  }  // 0-1023

  ClassDefOverride(SiWCaloPoint, 2)
};

#endif  // SND_SIWCALO_SIWCALOPOINT_H_
