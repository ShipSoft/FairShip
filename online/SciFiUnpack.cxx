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
                           // 1  - 2  - 3  : plane 1  or SciFiID:
                           // 4  - 5  - 6  : plane 2  or SciFiID:
                           // 7  - 8  - 9  : plane 3  or SciFiID:
                           // 10 - 11 - 12 : plane 4  or SciFiID:
                           // 13 - 14 - 15 : plane 5  or SciFiID:
                           // 16 - 17 - 18 : plane 6  or SciFiID:
                           // 19 - 20 - 21 : plane 7  or SciFiID:
                           // 22 - 23 - 24 : plane 8  or SciFiID:
};
struct ChannelId {
   uint16_t channel : 11; // 0 - 1536
   uint16_t board : 5;    // 0 - 23
};
struct SciFiDataFrame {
   DataFrameHeader header;
   HitData hits[0];
   int getHitCount() { return (header.size - sizeof(header)) / sizeof(HitData); }
};

// SciFiUnpack
SciFiUnpack::SciFiUnpack(uint16_t PartitionId)
   : fRawData(new TClonesArray("SciFiHit")), fNHits(0), fNHitsTotal(0), fPartitionId(PartitionId)
{
}

// SciFiUnpack::SciFiUnpack() = default;
// SciFiUnpack: Constructor
// SciFiUnpack::SciFiUnpack(uint16_t PartitionId){}
// SciFiUnpack::SciFiUnpack(uint16_t PartitionId)
//  : fRawTrigger(new TClonesArray("SciFiHit")), fNTrigs(0), fNHitsTotal(0), fPartitionId(PartitionId) {}

// Virtual SciFiUnpack: Public method
SciFiUnpack::~SciFiUnpack() = default;

// Init: Public method
Bool_t SciFiUnpack::Init()
{
   Register();
   return kTRUE;
}

// Register: Protected method
void SciFiUnpack::Register()
{

   LOG(INFO) << "SciFiUnpack : Registering..." << FairLogger::endl;
   auto *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("Digi_SciFiHits", "SciFi", fRawData, kTRUE);
   // fMan->Register("Digi_SciFiTrigger", "SciFi", fRawTrigger, kTRUE);
}

// DoUnpack: Public method
Bool_t SciFiUnpack::DoUnpack(Int_t *data, Int_t size)
{
   int module;
   int channel_number;
   int flag;
   UInt_t time;
   UShort_t finetime;
   uint64_t hitword;

   //  TFile f("converted_v1.root","RECREATE");
   //  TTree *tree = new TTree("scifihits","Converted hits");
   //  tree->Branch("channel_number",&channel_number,"channel_number/I");
   //  tree->Branch("time",&time,"time/i");
   //  tree->Branch("finetime",&finetime,"finetime/s");
   //  tree->Branch("module",&module,"module/I");
   //  tree->Branch("flag",&flag,"flag/I");

   LOG(INFO) << "SciFiUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<SciFiDataFrame *>(data);
   switch (df->header.frameTime) {
   case SoS: LOG(INFO) << "SciFiUnpack: SoS frame." << FairLogger::endl; return kTRUE;
   case EoS: LOG(INFO) << "SciFiUnpack: EoS frame." << FairLogger::endl; return kTRUE;
   default: break;
   }
   int i = 0;
   assert(df->header.size == size);
   auto nhits = df->getHitCount();
   LOG(INFO) << nhits << " hits." << FairLogger::endl;
   std::vector<HitData> hits(df->hits, df->hits + nhits);
   // std::cout << df->header.size << "  " << size << "  " << nhits << std::endl;
   for (auto &&hitData : hits) {
      // auto channelId = reinterpret_cast<ChannelId *>(&(hit.channelId)); // I am not sure what this is doing
      auto triggerFlag = (hitData.ch >= 16000) ? 1 : 0;
      auto board = (triggerFlag == 1) ? (hitData.ch - 16000) : (hitData.ch / 512);
      auto module = board / 3;
      auto channel = (triggerFlag == 1 && module > 0) ? hitData.ch : hitData.ch / module;

      //                0                                 + 0-25 * 10**5       +  0-16025;
      auto detectorId = (fPartitionId % 0x0900) * pow(10, 7) + board * pow(10, 5) + channel;

      LOG(INFO) << std::hex << *reinterpret_cast<uint64_t *>(&hitData) << std::dec << FairLogger::endl;
      LOG(INFO) << hitData.ch << "\t" << hitData.time << "\t" << hitData.finetime << "\t" << hitData.flags
                << FairLogger::endl;

      bool trigflag = triggerFlag;

      new ((*fRawData)[fNHits]) SciFiHit(detectorId, 0, hitData.time, hitData.finetime, hitData.flags, trigflag);

      // new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitData->time, hitData->finetime, hitData->ch, boardId, module,
      // trigflag, hitData->flags); new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitData->time, hitData->finetime,
      // hitData->ch, 0, 0, trigflag, hitData->flags); else new ((*fRawData)[fNHits]) SciFiHit(0x0900,0,
      // hitData->time*25, hitData->finetime*32./680,0, (hitData->ch-16000), (hitData->ch - 16000)/3, hitData->flags);
      // new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitData->time*25, hitData->finetime*32./680, channel, boardId,
      // module, hitData->flags); new ((*fRawData)[fNHits]) SciFiHit(detectorId,0, hitData->time * 25, hitData->finetime
      // * 32./680, hitData->ch, boardId, 0, trigflag);
      fNHits++;
   }

   fNHitsTotal += fNHits;
   // f.Write();
   return kTRUE;
}

// Reset: Public method
void SciFiUnpack::Reset()
{
   fRawData->Clear();
   fNHits = 0;
}

ClassImp(SciFiUnpack)
