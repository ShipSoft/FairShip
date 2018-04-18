#include "muonContFact.h"
#include "FairRuntimeDb.h"

#include <iostream>

ClassImp(muonContFact)

//static muonContFact gmuonContFact;

muonContFact::muonContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="muonContFact";
  fTitle="Factory for parameter containers in libmuon";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void muonContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the muon library.
  */
/*
  FairContainer* p= new FairContainer("muonGeoPar",
                                      "muon Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
 }

FairParSet* muonContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
      For an actual context, which is not an empty string and not
      the default context
      of this container, the name is concatinated with the context.
  */
 /* const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"muonGeoPar")==0) {
    p=new muonGeoPar(c->getConcatName().Data(),
                            c->GetTitle(),c->getContext());
  }
  return p;
*/
   return 0;
}
