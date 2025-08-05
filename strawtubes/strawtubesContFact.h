#ifndef STRAWTUBES_STRAWTUBESCONTFACT_H_
#define STRAWTUBES_STRAWTUBESCONTFACT_H_

#include "FairContFact.h"

class FairContainer;

class strawtubesContFact : public FairContFact
{
  private:
    void setAllContainers();
  public:
    strawtubesContFact();
    ~strawtubesContFact() {}
    FairParSet* createContainer(FairContainer*);
    ClassDef( strawtubesContFact,0) // Factory for all strawtubes parameter containers
};

#endif  // STRAWTUBES_STRAWTUBESCONTFACT_H_
