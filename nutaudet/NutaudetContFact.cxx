//*-- AUTHOR : Denis Bertini
//*-- Created : 21/06/2005

/////////////////////////////////////////////////////////////
//
//  NutaudetContFact
//
//  Factory for the parameter containers in libnutaudet
//
/////////////////////////////////////////////////////////////
#include "NutaudetContFact.h"

#include "FairRuntimeDb.h"              // for FairRuntimeDb

#include "TList.h"                      // for TList
#include "TString.h"                    // for TString

#include <string.h>                     // for strcmp, NULL

class FairParSet;

using namespace std;

ClassImp(NutaudetContFact)

//static NutaudetContFact gNutaudetContFact;

NutaudetContFact::NutaudetContFact()
  : FairContFact()
{
  // Constructor (called when the library is loaded)
  fName="NutaudetContFact";
  fTitle="Factory for parameter containers in libTauSensitive";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void NutaudetContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted contexts and adds them to
   *  the list of containers for the STS library.*/

  FairContainer* p= new FairContainer("FairGeoTauSensitivePar",
                                      "TauSensitive Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
}

FairParSet* NutaudetContFact::createContainer(FairContainer* c)
{
  /** Calls the constructor of the corresponding parameter container.
   * For an actual context, which is not an empty string and not the default context
   * of this container, the name is concatinated with the context. */
 /* const char* name=c->GetName();
  FairParSet* p=NULL;
  if (strcmp(name,"FairGeoTauSensitivePar")==0) {
    p=new FairGeoTauSensitivePar(c->getConcatName().Data(),c->GetTitle(),c->getContext());
  }
  return p;
*/
   return 0;
}

