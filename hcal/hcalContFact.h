#ifndef HCAL_HCALCONTFACT_H_
#define HCAL_HCALCONTFACT_H_

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

#endif  // HCAL_HCALCONTFACT_H_
