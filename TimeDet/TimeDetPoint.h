// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef TIMEDET_TIMEDETPOINT_H_
#define TIMEDET_TIMEDETPOINT_H_

#include <array>

#include "DetectorPoint.h"
#include "TObject.h"
#include "TVector3.h"

class TimeDetPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  TimeDetPoint();

  using SHiP::DetectorPoint::DetectorPoint;

  /** Destructor **/
  ~TimeDetPoint() override;

  void extraPrintInfo() const override;

 private:
  ClassDefOverride(TimeDetPoint, 4)
};

#endif  // TIMEDET_TIMEDETPOINT_H_
