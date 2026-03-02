// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef TIMEDET_TIMEDETPOINT_H_
#define TIMEDET_TIMEDETPOINT_H_ 1

#include <array>

#include "DetectorPoint.h"
#include "TObject.h"
#include "TVector3.h"

class TimeDetPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  TimeDetPoint();

  using SHiP::DetectorPoint::DetectorPoint;

  TimeDetPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
               Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode,
               TVector3 Lpos, TVector3 Lmom);

  /** Destructor **/
  virtual ~TimeDetPoint();

  void setDetectorName() override;
  void extraPrintInfo() const override;

 private:

  ClassDefOverride(TimeDetPoint, 3)
};

#endif  // TIMEDET_TIMEDETPOINT_H_
