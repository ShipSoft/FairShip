// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef DETECTOR_DETECTORPOINT_H_
#define DETECTOR_DETECTORPOINT_H_

#include <array>

#include "FairMCPoint.h"
#include "TVector3.h"

namespace SHiP {
class DetectorPoint : public FairMCPoint {
 public:
  DetectorPoint() = default;
  ~DetectorPoint() = default;

  DetectorPoint(Int_t eventID, Int_t trackID, Int_t detID, TVector3 pos,
                TVector3 mom, Double_t tof, Double_t length, Double_t eLoss,
                Int_t pdgCode, TVector3 Lpos, TVector3 Lmom);

  DetectorPoint(Int_t eventID, Int_t trackID, Int_t detID, TVector3 pos,
                TVector3 mom, Double_t tof, Double_t length, Double_t eLoss,
                Int_t pdgCode);

  /** Copy constructor **/
  DetectorPoint(const DetectorPoint& point) = default;
  DetectorPoint& operator=(const DetectorPoint& point) = default;

  /** Output to screen **/
  using FairMCPoint::Print;
  virtual void Print() const;
  Int_t PdgCode() const { return fPdgCode; }
  TVector3 LastPoint() const { return TVector3(fLpos[0], fLpos[1], fLpos[2]); }
  TVector3 LastMom() const { return TVector3(fLmom[0], fLmom[1], fLmom[2]); }

  virtual void extraPrintInfo() const;

 protected:
  Int_t fPdgCode;
  std::array<Double_t, 3> fLpos, fLmom;

 private:
  ClassDef(SHiP::DetectorPoint, 1);
};
}  // namespace SHiP

#endif  // DETECTOR_DETECTORPOINT_H_
