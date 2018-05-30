#include <cassert>

// ROOT headers
#include "TClonesArray.h"
#include "ROOT/TSeq.hxx"

// Fair headers
#include "FairRootManager.h"
#include "FairRunOnline.h"
#include "FairLogger.h"

// SHiP headers
#include "ShipTdcUnpack.h"
#include "ShipHit.h"
#include "ShipOnlineDataFormat.h"

// ShipTdcUnpack: Constructor
ShipTdcUnpack::ShipTdcUnpack(Short_t type, Short_t subType, Short_t procId, Short_t subCrate, Short_t control)
   : FairUnpack(type, subType, procId, subCrate, control), fRawData(new TClonesArray("ShipHit")), fNHits(0),
     fNHitsTotal(0)
{
}

// Virtual ShipTdcUnpack: Public method
ShipTdcUnpack::~ShipTdcUnpack()
{
   LOG(INFO) << "ShipTdcUnpack: Delete instance" << FairLogger::endl;
   delete fRawData;
}

// Init: Public method
Bool_t ShipTdcUnpack::Init()
{
   Register();
   return kTRUE;
}

// Register: Protected method
void ShipTdcUnpack::Register()
{
   //  LOG(DEBUG) << "Registering" << FairLogger::endl;
   LOG(INFO) << "ShipTdcUnpack : Registering..." << FairLogger::endl;
   FairRootManager *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("DriftTubesHit", "TDC", fRawData, kTRUE);
}

// DoUnpack: Public method
Bool_t ShipTdcUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(DEBUG) << "ShipTdcUnpack : Unpacking frame... size = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   assert(df->header.size == size);
   auto nhits = df->getHitCount();
   for (int i : ROOT::MakeSeq(nhits)) {
      auto channel = df->hits[i].channelId;
      auto time = df->hits[i].hitTime;
      new ((*fRawData)[fNHits]) ShipHit(channel, time);
      fNHits++;
   }

   assert(fRawData->GetEntries() == nhits);
   assert(nhits == fNHits);

   fNHitsTotal += fNHits;

   return kTRUE;
}

// Reset: Public method
void ShipTdcUnpack::Reset()
{
   LOG(DEBUG) << "ShipTdcUnpack : Clearing Data Structure" << FairLogger::endl;
   fRawData->Clear();
   fNHits = 0;
}

ClassImp(ShipTdcUnpack)
