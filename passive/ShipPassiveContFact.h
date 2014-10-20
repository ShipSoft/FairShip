#ifndef PNDPASSIVECONTFACT_H
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

#endif  /* !PNDPASSIVECONTFACT_H */
