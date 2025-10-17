// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#ifndef PASSIVE_SHIPCHAMBER_H_
#define PASSIVE_SHIPCHAMBER_H_

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipChamber::Class, Bool_t, etc

#include <string>                       // for string

class ShipChamber : public FairModule
{
  public:
    explicit ShipChamber(const char* name, const char* Title="ShipChamber");
    ShipChamber();
    virtual ~ShipChamber();
    void ConstructGeometry();
    ClassDef(ShipChamber,1)
    Int_t InitMedium(const char* name);

};

#endif  // PASSIVE_SHIPCHAMBER_H_
