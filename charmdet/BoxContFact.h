#ifndef CHARMDET_BOXCONTFACT_H_
#define CHARMDET_BOXCONTFACT_H_

#include "FairContFact.h"   // for FairContFact, etc
#include "Rtypes.h"         // for ShipPassiveContFact::Class, etc

class FairParSet;

class BoxContFact : public FairContFact
{
  private:
    void setAllContainers();

  public:
    BoxContFact();
    ~BoxContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef(BoxContFact, 0)   // Factory for all Passive parameter containers
};

#endif  // CHARMDET_BOXCONTFACT_H_
