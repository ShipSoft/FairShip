// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef MUON_MUONCONTFACT_H_
#define MUON_MUONCONTFACT_H_

#include "FairContFact.h"

class FairContainer;

class muonContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    muonContFact();
    ~muonContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( muonContFact,0) // Factory for all muon parameter containers
};

#endif  // MUON_MUONCONTFACT_H_
