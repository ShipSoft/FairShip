// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef PASSIVE_SHIPPASSIVECONTFACT_H_
#define PASSIVE_SHIPPASSIVECONTFACT_H_
#define PNDPASSIVECONTFACT_H

#include "FairContFact.h"               // for FairContFact, etc

#include "Rtypes.h"                     // for ShipPassiveContFact::Class, etc

class FairParSet;

class ShipPassiveContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    ShipPassiveContFact();
    ~ShipPassiveContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( ShipPassiveContFact,0) // Factory for all Passive parameter containers
};

#endif  // PASSIVE_SHIPPASSIVECONTFACT_H_
