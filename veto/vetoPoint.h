// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef VETO_VETOPOINT_H_
#define VETO_VETOPOINT_H_

#include <array>

#include "DetectorPoint.h"
#include "TObject.h"
#include "TVector3.h"

class vetoPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  vetoPoint();

  using SHiP::DetectorPoint::DetectorPoint;
  /** Constructor with arguments
   *@param trackID  Index of MCTrack
   *@param detID    Detector ID
                    // for LiSc: segment T1 (seg=1), segment T2 (seg=2), normal
   detector (c=0) and corner detector (c=1), sequential number
                    //  nr + 100000*seg + 10000*c;
   *@param pos      Ccoordinates at entrance to active volume [cm]
   *@param mom      Momentum of track at entrance [GeV]
   *@param tof      Time since event start [ns]
   *@param length   Track length since creation [cm]
   *@param eLoss    Energy deposit [GeV]
   **/

  /** Destructor **/
  ~vetoPoint() override;

  void extraPrintInfo() const override;

  /** Output to screen **/

 private:
  ClassDefOverride(vetoPoint, 5)
};

#endif  // VETO_VETOPOINT_H_
