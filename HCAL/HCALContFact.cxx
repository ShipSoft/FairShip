// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#include "HCALContFact.h"
#include "FairRuntimeDb.h"

#include <iostream>


//static HCALContFact gHCALContFact;

HCALContFact::HCALContFact()
  : FairContFact()
{
  /** Constructor (called when the library is loaded) */
  fName="HCALContFact";
  fTitle="Factory for parameter containers in libHCAL";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void HCALContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted
      contexts and adds them to
      the list of containers for the HCAL library.
  */
/*
  FairContainer* p= new FairContainer("HCALGeoPar",
                                      "HCAL Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
*/
 }

FairParSet* HCALContFact::createContainer(FairContainer* c)
{
    /** Calls the constructor of the corresponding parameter container.
        For an actual context, which is not an empty string and not
        the default context
        of this container, the name is concatenated with the context.
    */
    /* const char* name=c->GetName();
     FairParSet* p=NULL;
     if (strcmp(name,"HCALGeoPar")==0) {
       p=new HCALGeoPar(c->getConcatName().Data(),
                               c->GetTitle(),c->getContext());
     }
     return p;
   */
    return 0;
}
