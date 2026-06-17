// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// -------------------------------------------------------------------------
// -----                    ShipBellField header file                  -----
// -----                Created 25/03/14  by M. Al-Turany              -----
// -------------------------------------------------------------------------

/** ShipBellField.h
 ** @author M.Al-Turany <m.al/turany@gsi.de>
 ** @since 25.03.2014
 ** @version1.0
 **
 ** A parametrized magnetic field
 ** Bpeak/(1+abs((z-zmiddle)/2.1)**6)
 **/

#ifndef FIELD_SHIPBELLFIELD_H_
#define FIELD_SHIPBELLFIELD_H_

#include "FairField.h"

class ShipFieldPar;

class ShipBellField : public FairField {
 public:
  /** Default constructor **/
  ShipBellField();

  /** Standard constructor
   ** @param name   Object name
   ** @param Bpeak       peak field..
   ** @param Zmiddle     middle of the magnet (global coordinates)
   ** @param Btube      largest radius of the tube ellips (inside)
   **/
  explicit ShipBellField(const char* name, Double_t Bpeak, Double_t Zmiddle,
                         Int_t fOrient = 1, Double_t Btube = 500.);

  /** Constructor from ShipFieldPar **/
  explicit ShipBellField(ShipFieldPar* fieldPar);

  /** Destructor **/
  ~ShipBellField() override;

  /** Get components of field at a given point
   ** @param x,y,z   Point coordinates [cm]
   **/
  Double_t GetBx(Double_t x, Double_t y, Double_t z) override;
  Double_t GetBy(Double_t x, Double_t y, Double_t z) override;
  Double_t GetBz(Double_t x, Double_t y, Double_t z) override;

  void IncludeTarget(Double_t xy, Double_t z, Double_t l);

  /** Screen output **/
  void Print(Option_t* = "") const override;

 private:
  /** Field parameters **/
  Double_t fPeak;
  Double_t fMiddle;
  Double_t fBtube;
  Int_t fOrient;
  Bool_t fInclTarget;
  Double_t targetXY;
  Double_t targetZ0;
  Double_t targetL;

  ClassDefOverride(ShipBellField, 2);
};

#endif  // FIELD_SHIPBELLFIELD_H_
