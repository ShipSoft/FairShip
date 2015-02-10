#ifndef NUTAUDETCONTFACT_H
#define NUTAUDETCONTFACT_H

#include "FairContFact.h"               // for FairContFact, etc

#include "Rtypes.h"                     // for ShipPassiveContFact::Class, etc

class FairParSet;

class NutaudetContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    NutaudetContFact();
    ~NutaudetContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef(NutaudetContFact,0) // Factory for all Passive parameter containers
};

#endif  /* !PNDPASSIVECONTFACT_H */
