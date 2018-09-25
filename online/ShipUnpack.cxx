#include <cassert>

// ROOT headers
#include "TClonesArray.h"

// Fair headers
#include "FairLogger.h"
#include "FairRootManager.h"

// SHiP headers
#include "ShipUnpack.h"

// ShipUnpack: Constructor
ShipUnpack::ShipUnpack(Short_t type, Short_t subType, Short_t procId, Short_t subCrate, Short_t control)
   : FairUnpack(type, subType, procId, subCrate, control), fRawData(new TClonesArray()), fNHits(0), fNHitsTotal(0),
     fPartitionId(-1)
{
}

// Virtual ShipUnpack: Public method
ShipUnpack::~ShipUnpack()
{
   LOG(INFO) << "ShipUnpack: Delete instance" << FairLogger::endl;
   delete fRawData;
}

Bool_t ShipUnpack::DoUnpack(Int_t *, Int_t)
{
   return kTRUE;
}

// Init: Public method
Bool_t ShipUnpack::Init()
{
   Register();
   return kTRUE;
}

// Reset: Public method
void ShipUnpack::Reset() {}

void ShipUnpack::Register()
{
   LOG(INFO) << "ShipUnpack : Registering..." << FairLogger::endl;
   auto *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
}

ClassImp(ShipUnpack)
