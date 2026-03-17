// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef DETECTOR_DETECTORHIT_H_
#define DETECTOR_DETECTORHIT_H_

#include "Rtypes.h"    // for Double_t, Int_t, Float_t, etc
#include "TObject.h"   //
#include "TVector3.h"  // for TVector3

namespace SHiP {
/**
 * copied from FairRoot FairHit and simplified
 */
class DetectorHit : public TObject {
 public:
  /** Default constructor **/
  DetectorHit();

  /** Constructor with hit parameters **/
  DetectorHit(Int_t detID, Float_t digi);

  /** Destructor **/
  ~DetectorHit() override = default;

  /** Accessors **/
  Double_t GetDigi() const { return fdigi; };
  Int_t GetDetectorID() const { return fDetectorID; };

  /** Modifiers **/
  void SetDigi(Float_t d) { fdigi = d; }
  void SetDetectorID(Int_t detID) { fDetectorID = detID; }

  /*** Output to screen */
  void Print(const Option_t* opt = "") const override {}

 protected:
  Float_t fdigi;      ///< digitized detector hit
  Int_t fDetectorID;  ///< Detector unique identifier

  ClassDefOverride(SHiP::DetectorHit, 1);
};
}  // namespace SHiP

#endif  // DETECTOR_DETECTORHIT_H_
