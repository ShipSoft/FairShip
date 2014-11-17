#ifndef HCALCONTFACT_H
#define HCALCONTFACT_H

#include "FairContFact.h"

class FairContainer;

class hcalContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    hcalContFact();
    ~hcalContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( hcalContFact,0) // Factory for all hcal parameter containers
};

#endif
