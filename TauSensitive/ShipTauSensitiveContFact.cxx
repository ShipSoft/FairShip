//*-- AUTHOR : Denis Bertini
//*-- Created : 21/06/2005

/////////////////////////////////////////////////////////////
//
//  ShipTauSensitiveContFact
//
//  Factory for the parameter containers in libTauSensitive
//
/////////////////////////////////////////////////////////////
#include "ShipTauSensitiveContFact.h"

#include "FairRuntimeDb.h"              // for FairRuntimeDb

#include "TList.h"                      // for TList
#include "TString.h"                    // for TString

#include <string.h>                     // for strcmp, NULL

class FairParSet;

using namespace std;

ClassImp(ShipTauSensitiveContFact)

static ShipTauSensitiveContFact gShipTauSensitiveContFact;

ShipTauSensitiveContFact::ShipTauSensitiveContFact()
  : FairContFact()
{
  // Constructor (called when the library is loaded)
  fName="ShipTauSensitiveContFact";
  fTitle="Factory for parameter containers in libTauSensitive";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void ShipTauSensitiveContFact::setAllContainers()
{
  /** Creates the Container objects with all accepted contexts and adds them to
   *  the list of containers for the STS library.*/

  FairContainer* p= new FairContainer("FairGeoTauSensitivePar",
                                      "TauSensitive Geometry Parameters",
                                      "TestDefaultContext");
  p->addContext("TestNonDefaultContext");

  containers->Add(p);
}

FairParSet* ShipTauSensitiveContFact::createContainer(FairContainer* c)
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

