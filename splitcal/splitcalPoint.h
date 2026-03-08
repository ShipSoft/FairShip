// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SPLITCAL_SPLITCALPOINT_H_
#define SPLITCAL_SPLITCALPOINT_H_

#include "DetectorPoint.h"
#include "TObject.h"
#include "TVector3.h"

class splitcalPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  splitcalPoint();

  using SHiP::DetectorPoint::DetectorPoint;

  /** Destructor **/
  virtual ~splitcalPoint();

  static constexpr const char* BranchName = "splitcalPoint";
  const char* DetectorName() const override { return BranchName; }
  void extraPrintInfo() const override;

 private:
  ClassDefOverride(splitcalPoint, 4)
};

#endif  // SPLITCAL_SPLITCALPOINT_H_
