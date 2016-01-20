#ifndef VETOCONTFACT_H
#define VETOCONTFACT_H

#include "FairContFact.h"

class FairContainer;

class preshowerContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    preshowerContFact();
    ~preshowerContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( preshowerContFact,0) // Factory for all preshower parameter containers
};

#endif
