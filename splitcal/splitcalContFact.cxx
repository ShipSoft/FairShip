#include "splitcalContFact.h"
#include "FairRuntimeDb.h"

#include <iostream>

ClassImp(splitcalContFact)

//static splitcalContFact gsplitcalContFact;

splitcalContFact::splitcalContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="splitcalContFact";
  fTitle="Factory for parameter containers in libsplitcal";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void splitcalContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the splitcal library.
  */
/*
  FairContainer* p= new FairContainer("splitcalGeoPar",
                                      "splitcal Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
 }

FairParSet* splitcalContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
      For an actual context, which is not an empty string and not
      the default context
      of this container, the name is concatinated with the context.
  */
 /* const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"splitcalGeoPar")==0) {
    p=new splitcalGeoPar(c->getConcatName().Data(),
                            c->GetTitle(),c->getContext());
  }
  return p;
*/
   return 0;
}
