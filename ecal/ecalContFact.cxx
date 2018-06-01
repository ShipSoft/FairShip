#include "ecalContFact.h"


#include "FairRuntimeDb.h"

#include <iostream>

ClassImp(ecalContFact)

//static ecalContFact gecalContFact;

ecalContFact::ecalContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="ecalContFact";
  fTitle="Factory for parameter containers in libecal";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void ecalContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the ecal library.
  */

 /* FairContainer* p= new FairContainer("ecalGeoPar",
                                      "ecal Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
}

FairParSet* ecalContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
      For an actual context, which is not an empty string and not
      the default context
      of this container, the name is concatinated with the context.
  */
    /*
  const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"ecalGeoPar")==0) {
    p=new ecalGeoPar(c->getConcatName().Data(),
                            c->GetTitle(),c->getContext());
  }
  return p;
     */
   return 0;
}
