// ROOT headers
#include "TClonesArray.h"

// SHiP headers
#include "SciFiUnpack.h"
#include "SciFiHit.h"
#include "ShipOnlineDataFormat.h"

// Fair headers
#include "FairRootManager.h"
#include "FairRunOnline.h"
#include "FairLogger.h"

struct HitData {
   uint64_t flags : 2;     // flags
   uint64_t finetime : 16; // fine time
   uint64_t time : 32;     // time
   uint64_t ch : 14;       // channel from signal or trigger
                           // if signal: channel ranges [0 - 1536] * nop
                           // where nop = number of planes
                           // if trigger: channel ranges from [1 - 24]
                           // which corresponds to the board number
                           // 1  - 2  - 3  : plane 1  or SciFiID: 111
                           // 4  - 5  - 6  : plane 2  or SciFiID: 112
                           // 7  - 8  - 9  : plane 3  or SciFiID: 121
                           // 10 - 11 - 12 : plane 4  or SciFiID: 122
                           // 13 - 14 - 15 : plane 5  or SciFiID: 131
                           // 16 - 17 - 18 : plane 6  or SciFiID: 132
                           // 19 - 20 - 21 : plane 7  or SciFiID: 141
                           // 22 - 23 - 24 : plane 8  or SciFiID: 142
};

struct SciFiDataFrame {
   DataFrameHeader header;
   HitData hits[0];
   int getHitCount() { return (header.size - sizeof(header)) / sizeof(HitData); }
};

SciFiUnpack::SciFiUnpack(uint16_t PartitionId) : fRawData(new TClonesArray("SciFiHit")) {}

SciFiUnpack::~SciFiUnpack() = default;

Bool_t SciFiUnpack::Init()
{
   Register();
   return kTRUE;
}

void SciFiUnpack::Register()
{

   LOG(INFO) << "SciFiUnpack : Registering..." << FairLogger::endl;
   auto *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("Digi_SciFiHits", "SciFi", fRawData.get(), kTRUE);
   // fMan->Register("Digi_SciFiTrigger", "SciFi", fRawTrigger, kTRUE);
}

Bool_t SciFiUnpack::DoUnpack(Int_t *data, Int_t size)
{

   LOG(INFO) << "SciFiUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<SciFiDataFrame *>(data);
   switch (df->header.frameTime) {
   case SoS: LOG(INFO) << "SciFiUnpack: SoS frame." << FairLogger::endl; return kTRUE;
   case EoS: LOG(INFO) << "SciFiUnpack: EoS frame." << FairLogger::endl; return kTRUE;
   default: break;
   }

   int i = 0;
   int layerID;
   assert(df->header.size == size);
   auto nhits = df->getHitCount();
   LOG(INFO) << nhits << " hits." << FairLogger::endl;
   std::vector<HitData> hits(df->hits, df->hits + nhits);
   // std::cout << df->header.size << "  " << size << "  " << nhits << std::endl;
   for (auto &&hitData : hits) {
     auto triggerFlag = (hitData.ch >= 16000) ? 1 : 0;
     auto board = (triggerFlag == 1) ? (hitData.ch - 15999) : (hitData.ch / 512 + 1);
     auto layer = (board-1) / 3 + 1;
     if (layer==1) layerID=111; 
     else if (layer==2) layerID=112; 
     else if (layer==3) layerID=121; 
     else if (layer==4) layerID=122; 
     else if (layer==5) layerID=131; 
     else if (layer==6) layerID=132; 
     else if (layer==7) layerID=141; 
     else layerID=142; 

     //                0-25 * 10**5       +  0-16025;
     auto detectorId = board * pow(10, 5) + hitData.ch;
     bool trigflag = triggerFlag;

     new ((*fRawData)[fNHits]) SciFiHit(detectorId, layerID, hitData.ch, board, hitData.time, hitData.finetime, hitData.flags, trigflag);

     fNHits++;
   }

   fNHitsTotal += fNHits;
   return kTRUE;

}

void SciFiUnpack::Reset()
{
  fRawData->Clear();
  fNHits = 0;
}

ClassImp(SciFiUnpack)
