// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// -------------------------------------------------------------------------
// -----                    ShipFieldCreator header file                  -----
// -----                Created 26/03/14  by M. Al-Turany              -----
// -------------------------------------------------------------------------

#ifndef FIELD_SHIPFIELDCREATOR_H_
#define FIELD_SHIPFIELDCREATOR_H_

#include "FairFieldFactory.h"

class ShipFieldPar;

class FairField;

class ShipFieldCreator : public FairFieldFactory {
 public:
  ShipFieldCreator();
  ~ShipFieldCreator() override;
  FairField* createFairField() override;
  void SetParm() override;
  ClassDefOverride(ShipFieldCreator, 1);

 protected:
  ShipFieldPar* fFieldPar;

 private:
  ShipFieldCreator(const ShipFieldCreator&) = delete;
  ShipFieldCreator& operator=(const ShipFieldCreator&) = delete;
};
#endif  // FIELD_SHIPFIELDCREATOR_H_
