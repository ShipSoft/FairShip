// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef STRAWTUBES_STRAWTUBESPOINT_H_
#define STRAWTUBES_STRAWTUBESPOINT_H_

#include "DetectorPoint.h"
#include "TObject.h"
#include "TVector3.h"

class strawtubesHit;

class strawtubesPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  strawtubesPoint();
  using SHiP::DetectorPoint::DetectorPoint;

  /** Constructor with arguments
   *@param trackID  Index of MCTrack
   *@param detID    Detector ID
   *@param pos      Ccoordinates at entrance to active volume [cm]
   *@param mom      Momentum of track at entrance [GeV]
   *@param tof      Time since event start [ns]
   *@param length   Track length since creation [cm]
   *@param eLoss    Energy deposit [GeV]
   **/
  strawtubesPoint(Int_t eventID, Int_t trackID, Int_t detID, TVector3 pos,
                  TVector3 mom, Double_t tof, Double_t length, Double_t eLoss,
                  Int_t pdgcode, Double_t dist);

  /** Destructor **/
  ~strawtubesPoint() override;

  /** Output to screen **/

  Double_t dist2Wire() const { return fdist2Wire; }
  void extraPrintInfo() const override;

 private:
  Double_t fdist2Wire;
  ClassDefOverride(strawtubesPoint, 5);
};

#endif  // STRAWTUBES_STRAWTUBESPOINT_H_
