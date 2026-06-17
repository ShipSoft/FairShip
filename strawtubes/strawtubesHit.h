// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef STRAWTUBES_STRAWTUBESHIT_H_
#define STRAWTUBES_STRAWTUBESHIT_H_

#include "DetectorHit.h"
#include "strawtubesPoint.h"

class strawtubesHit : public SHiP::DetectorHit {
 public:
  /** Default constructor **/
  strawtubesHit();

  /** Constructor with arguments
   *@param detID    Detector ID
   *@param digi      digitized/measured TDC
   *@param flag      True/False, false if there is another hit with smaller tdc
   **/
  strawtubesHit(Int_t detID, Float_t tdc);
  strawtubesHit(strawtubesPoint* p, Double_t t0);
  /** Destructor **/
  ~strawtubesHit() override = default;

  /** Accessors **/
  Int_t GetStationNumber() const;
  Int_t GetViewNumber() const;
  Int_t GetLayerNumber() const;
  Int_t GetStrawNumber() const;

  /** Output to screen **/
  using SHiP::DetectorHit::Print;
  void Print() const;
  Float_t GetTDC() const { return fdigi; }
  void setInvalid() { flag = false; }
  bool isValid() const { return flag; }

  /** Copy constructor **/
  strawtubesHit(const strawtubesHit& point) = default;
  strawtubesHit& operator=(const strawtubesHit& point) = default;

 private:
  Bool_t flag{true};  ///< validity flag

  ClassDefOverride(strawtubesHit, 6);
};

#endif  // STRAWTUBES_STRAWTUBESHIT_H_
