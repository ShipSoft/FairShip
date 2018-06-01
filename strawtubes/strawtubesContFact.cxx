#include "strawtubesContFact.h"
#include "FairRuntimeDb.h"

#include <iostream>

ClassImp(strawtubesContFact)

// static strawtubesContFact gstrawtubesContFact;

strawtubesContFact::strawtubesContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="strawtubesContFact";
  fTitle="Factory for parameter containers in libstrawtubes";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void strawtubesContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the strawtubes library.
  */
/*
  FairContainer* p= new FairContainer("strawtubesGeoPar",
                                      "strawtubes Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
 }

FairParSet* strawtubesContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
      For an actual context, which is not an empty string and not
      the default context
      of this container, the name is concatinated with the context.
  */
 /* const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"strawtubesGeoPar")==0) {
    p=new strawtubesGeoPar(c->getConcatName().Data(),
                            c->GetTitle(),c->getContext());
  }
  return p;
*/
  return 0;
  }
