#include "vetoContFact.h"
#include "FairRuntimeDb.h"

#include <iostream>

ClassImp(vetoContFact)

//static vetoContFact gvetoContFact;

vetoContFact::vetoContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="vetoContFact";
  fTitle="Factory for parameter containers in libveto";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void vetoContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the veto library.
  */
/*
  FairContainer* p= new FairContainer("vetoGeoPar",
                                      "veto Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
 }

FairParSet* vetoContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
      For an actual context, which is not an empty string and not
      the default context
      of this container, the name is concatinated with the context.
  */
 /* const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"vetoGeoPar")==0) {
    p=new vetoGeoPar(c->getConcatName().Data(),
                            c->GetTitle(),c->getContext());
  }
  return p;
*/
   return 0;
  }
