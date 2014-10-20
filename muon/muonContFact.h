#ifndef VETOCONTFACT_H
#define VETOCONTFACT_H

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

#endif
