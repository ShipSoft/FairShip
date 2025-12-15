// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef HCAL_HCALCONTFACT_H_
#define HCAL_HCALCONTFACT_H_

#include "FairContFact.h"

class FairContainer;

class HCALContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    HCALContFact();
    ~HCALContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( HCALContFact,0) // Factory for all HCAL parameter containers
};

#endif  
