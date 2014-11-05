#ifndef TAUSENSCONTFACT_H
#define TAUSENSCONTFACT_H

#include "FairContFact.h"               // for FairContFact, etc

#include "Rtypes.h"                     // for ShipPassiveContFact::Class, etc

class FairParSet;

class ShipTauSensitiveContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    ShipTauSensitiveContFact();
    ~ShipTauSensitiveContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( ShipTauSensitiveContFact,0) // Factory for all Passive parameter containers
};

#endif  /* !PNDPASSIVECONTFACT_H */
