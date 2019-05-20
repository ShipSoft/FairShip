#include "preshowerContFact.h"
#include "FairRuntimeDb.h"

#include <iostream>

ClassImp(preshowerContFact)

//static preshowerContFact gpreshowerContFact;

preshowerContFact::preshowerContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="preshowerContFact";
  fTitle="Factory for parameter containers in libpreshower";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void preshowerContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the preshower library.
  */
/*
  FairContainer* p= new FairContainer("preshowerGeoPar",
                                      "preshower Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
 }

FairParSet* preshowerContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
      For an actual context, which is not an empty string and not
      the default context
      of this container, the name is concatinated with the context.
  */
 /* const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"preshowerGeoPar")==0) {
    p=new preshowerGeoPar(c->getConcatName().Data(),
                            c->GetTitle(),c->getContext());
  }
  return p;
*/
   return 0;
}
