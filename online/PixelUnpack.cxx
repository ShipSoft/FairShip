#include <cassert>

// ROOT headers
#include "TClonesArray.h"

// Fair headers
#include "FairRootManager.h"
#include "FairRunOnline.h"
#include "FairLogger.h"

// SHiP headers
#include "PixelUnpack.h"
#include "ShipPixelHit.h"
#include "ShipOnlineDataFormat.h"

struct HitData {
   uint16_t relative_BCID : 4;
   uint16_t flags : 4;
   uint16_t moduleID : 4;
   uint16_t tot : 4;
};
struct ChannelId {
   uint16_t column : 7;
   uint16_t row : 9;
};

// PixelUnpack: Constructor
PixelUnpack::PixelUnpack(uint16_t PartitionId)
   : fRawData(new TClonesArray("ShipPixelHit")), fNHits(0), fNHitsTotal(0), fPartitionId(PartitionId)
{
}

// Virtual PixelUnpack: Public method
PixelUnpack::~PixelUnpack()
{
   LOG(INFO) << "PixelUnpack: Delete instance" << FairLogger::endl;
   delete fRawData;
}

// Init: Public method
Bool_t PixelUnpack::Init()
{
   Register();
   return kTRUE;
}

// Register: Protected method
void PixelUnpack::Register()
{
   LOG(INFO) << "PixelUnpack : Registering..." << FairLogger::endl;
   auto *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("Digi_PixelHits", "Pixels", fRawData, kTRUE);
}

// DoUnpack: Public method
Bool_t PixelUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(INFO) << "PixelUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   switch (df->header.frameTime) {
   case SoS: LOG(INFO) << "PixelUnpacker: SoS frame." << FairLogger::endl; return kTRUE;
   case EoS: LOG(INFO) << "PixelUnpacker: EoS frame." << FairLogger::endl; return kTRUE;
   default: break;
   }
   assert(df->header.size == size);
   auto nhits = df->getHitCount();
   std::vector<RawDataHit> hits(df->hits, df->hits + nhits);
   for (auto &&hit : hits) {
      auto hitData = reinterpret_cast<HitData *>(&(hit.hitTime));
      auto channelId = reinterpret_cast<ChannelId *>(&(hit.channelId));
      auto detectorID = (df->header.partitionId%0x0800) * 10000000 + 1000000 * hitData->moduleID + 1000 * channelId->row + channelId->column;
      auto tot = hitData->tot;
      new ((*fRawData)[fNHits]) ShipPixelHit(detectorID, tot); //tot is measured in steps of 25 ns
      fNHits++;
   }

   fNHitsTotal += fNHits;
   return kTRUE;
}

// Reset: Public method
void PixelUnpack::Reset()
{
   LOG(DEBUG) << "PixelUnpack : Clearing Data Structure" << FairLogger::endl;
   fRawData->Clear();
   fNHits = 0;
}

ClassImp(PixelUnpack)
