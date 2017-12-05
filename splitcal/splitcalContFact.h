#ifndef VETOCONTFACT_H
#define VETOCONTFACT_H

#include "FairContFact.h"

class FairContainer;

class splitcalContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    splitcalContFact();
    ~splitcalContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( splitcalContFact,0) // Factory for all splitcal parameter containers
};

#endif
