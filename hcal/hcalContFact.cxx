#include "hcalContFact.h"


#include "FairRuntimeDb.h"

#include <iostream>

ClassImp(hcalContFact)

//static hcalContFact ghcalContFact;

hcalContFact::hcalContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="hcalContFact";
  fTitle="Factory for parameter containers in libhcal";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void hcalContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the hcal library.
  */

 /* FairContainer* p= new FairContainer("hcalGeoPar",
                                      "hcal Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
}

FairParSet* hcalContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
      For an actual context, which is not an empty string and not
      the default context
      of this container, the name is concatinated with the context.
  */
    /*
  const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"hcalGeoPar")==0) {
    p=new hcalGeoPar(c->getConcatName().Data(),
                            c->GetTitle(),c->getContext());
  }
  return p;
     */
   return 0;
}
