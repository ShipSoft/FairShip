#ifndef BOXCONTFACT_H
#define BOXCONTFACT_H

#include "FairContFact.h"               // for FairContFact, etc

#include "Rtypes.h"                     // for ShipPassiveContFact::Class, etc

class FairParSet;

class EmulsionDetContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    EmulsionDetContFact();
    ~EmulsionDetContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef(EmulsionDetContFact,0) // Factory for all Passive parameter containers
};

#endif  /* !PNDPASSIVECONTFACT_H */
