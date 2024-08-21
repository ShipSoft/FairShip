#ifndef VETO_VETOCONTFACT_H_
#define VETO_VETOCONTFACT_H_

#include "FairContFact.h"

class FairContainer;

class vetoContFact : public FairContFact
{
  private:
    void setAllContainers();

  public:
    vetoContFact();
    ~vetoContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef(vetoContFact, 0)   // Factory for all veto parameter containers
};

#endif   // VETO_VETOCONTFACT_H_
