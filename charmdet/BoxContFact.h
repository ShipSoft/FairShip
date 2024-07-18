#ifndef BOXCONTFACT_H
#define BOXCONTFACT_H

#include "FairContFact.h"               // for FairContFact, etc

#include "Rtypes.h"                     // for ShipPassiveContFact::Class, etc

class FairParSet;

class BoxContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    BoxContFact();
    ~BoxContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef(BoxContFact,0) // Factory for all Passive parameter containers
};

#endif  /* !PNDPASSIVECONTFACT_H */
