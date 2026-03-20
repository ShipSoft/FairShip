// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef TIMEDET_TIMEDET_H_
#define TIMEDET_TIMEDET_H_

#include <map>
#include <vector>

#include "Detector.h"
#include "TLorentzVector.h"
#include "TVector3.h"

class TimeDetPoint;
class FairVolume;
class TClonesArray;

class TimeDet : public SHiP::Detector<TimeDetPoint> {
 public:
  /**      Name :  Detector Name
   *       Active: kTRUE for active detectors (ProcessHits() will be called)
   *               kFALSE for inactive detectors
   */
  TimeDet(const char* Name, Bool_t Active);

  /** default constructor */
  TimeDet();

  /**   this method is called for each step during simulation
   *    (see FairMCApplication::Stepping())
   */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  /** Sets detector position along z */
  void SetZposition(Double_t z) { fzPos = z; }
  void SetBarZspacing(Double_t row, Double_t column) {
    fdzBarRow = row;
    fdzBarCol = column;
  }
  void SetBarZ(Double_t dz) { fzBar = dz; }
  void SetSizeX(Double_t x) { fxSize = x; }
  void SetSizeY(Double_t y) { fySize = y; }

  double GetXCol(int ic) const;
  double GetYRow(int ir) const;
  void GetBarRowCol(int ib, int& irow, int& icol) const;
  double GetZBar(int ir, int ic) const;

  /**  Create the detector geometry */
  void ConstructGeometry() override;

 private:
  /** Detector parameters.*/
  Double_t fzPos;  //!  z-position of veto station

  Double_t fxSize;  //! width of the detector
  Double_t fySize;  //! height of the detector

  Double_t fxBar;  //! length of the bar
  Double_t fyBar;  //! width of the bar
  Double_t fzBar;  //! depth of the bar

  Double_t fdzBarCol;  //! z-distance between columns
  Double_t fdzBarRow;  //! z-distance between rows

  Int_t fNCol;  //! Number of columns
  Int_t fNRow;  //! Number of rows

  Double_t fxCenter;  //! x-position of the detector center
  Double_t fyCenter;  //! y-position of the detector center

  Int_t fNBars;   //! Number of bars
  Double_t fxOv;  //! Overlap along x
  Double_t fyOv;  //! Overlap along y

  TimeDet(const TimeDet&) = delete;
  TimeDet& operator=(const TimeDet&) = delete;

  ClassDefOverride(TimeDet, 5)
};

#endif  // TIMEDET_TIMEDET_H_
