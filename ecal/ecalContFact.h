// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#ifndef ECAL_ECALCONTFACT_H_
#define ECAL_ECALCONTFACT_H_

#include "FairContFact.h"

class FairContainer;

class ecalContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    ecalContFact();
    ~ecalContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( ecalContFact,0) // Factory for all ecal parameter containers
};

#endif  // ECAL_ECALCONTFACT_H_
