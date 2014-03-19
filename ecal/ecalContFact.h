#ifndef ECALCONTFACT_H
#define ECALCONTFACT_H

#include "FairContFact.h"

class FairContainer;

class ecalContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    ecalContFact();
    ~ecalContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( ecalContFact,0) // Factory for all ecal parameter containers
};

#endif
