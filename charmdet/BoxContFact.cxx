//*-- AUTHOR : Denis Bertini
//*-- Created : 21/06/2005

/////////////////////////////////////////////////////////////
//
//  BoxContFact
//
//  Factory for the parameter containers in libnutaudet
//
/////////////////////////////////////////////////////////////
#include "BoxContFact.h"

#include "FairRuntimeDb.h"              // for FairRuntimeDb

#include "TList.h"                      // for TList
#include "TString.h"                    // for TString

#include <string.h>                     // for strcmp, NULL

class FairParSet;

using namespace std;

ClassImp(BoxContFact)

static BoxContFact gBoxContFact;

BoxContFact::BoxContFact()
  : FairContFact()
{
  // Constructor (called when the library is loaded)
  fName="BoxContFact";
  fTitle="Factory for parameter containers in libBOxSensitive";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void BoxContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted contexts and adds them to
   *  the list of containers for the STS library.*/

  FairContainer* p= new FairContainer("FairGeoBoxSensitivePar",
                                      "BoxSensitive Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
}

FairParSet* BoxContFact::createContainer(FairContainer* c)
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

