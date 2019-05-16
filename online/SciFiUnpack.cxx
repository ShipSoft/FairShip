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
   uint64_t hitword;
};

struct SciFiInfo{
  uint64_t ch       : 14; // channel from signal or trigger
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
  uint64_t time     : 32; // time
  uint64_t finetime : 16; // fine time
  uint64_t flags    : 2 ; // flags
};
//SciFiUnpack::SciFiUnpack() = default; 
// SciFiUnpack: Constructor
//SciFiUnpack::SciFiUnpack(uint16_t PartitionId){}
SciFiUnpack::SciFiUnpack(uint16_t PartitionId) 
  : fRawData(new TClonesArray("SciFiHit")), fNHits(0), fNHitsTotal(0), fPartitionId(PartitionId) {}
//SciFiUnpack::SciFiUnpack(uint16_t PartitionId) 
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
void SciFiUnpack::Register(){

   LOG(INFO) << "SciFiUnpack : Registering..." << FairLogger::endl;
   auto *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("Digi_SciFiHits", "SciFi", fRawData, kTRUE);
   //fMan->Register("Digi_SciFiTrigger", "SciFi", fRawTrigger, kTRUE);
}

// DoUnpack: Public method
Bool_t SciFiUnpack::DoUnpack(Int_t *data, Int_t size)
{
  int nTriggers = 0;
  int nHits = 0;
  //uint64_t aux[6];
  //aux[0]   = 0x000000000000001F;
  //aux[1]   = 0X0000000FFFFFFFFF;
  //aux[2]   = 0X00000000000000FF;
  //aux[3]   = 0X000000000000003F;
  //aux[4]   = 0X0000000000000007;
  //aux[5]   = 0X0000000000000001;


  LOG(INFO) << "SciFiUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;
  auto df = reinterpret_cast<DataFrame *>(data);
  switch (df->header.frameTime) {
    case SoS: LOG(INFO) << "SciFiUnpack: SoS frame." << FairLogger::endl; return kTRUE;
    case EoS: LOG(INFO) << "SciFiUnpack: EoS frame." << FairLogger::endl; return kTRUE;
    default: break;
  }

  assert(df->header.size == size);
  auto nhits = df->getHitCount();
  std::vector<RawDataHit> hits(df->hits, df->hits + nhits);
  std::cout << df->header.size << "  " << size << "  " << nhits << std::endl;
  for (auto &&hit : hits) {
    auto hitData = reinterpret_cast<HitData *>(&(hit.hitTime));
    //   //auto channelId = reinterpret_cast<ChannelId *>(&(hit.channelId));
    //   //auto detectorId = 1000000 * hitData->moduleID + 1000 * channelId->row + channelId->column;
    auto hitinfo = hitData->hitword;
    SciFiInfo scifihit;
    scifihit.ch       = (hitinfo >> 50);
    scifihit.time     = (hitinfo >> 18) & 0X00000000FFFFFFFF;
    scifihit.finetime = (hitinfo >> 2 ) & 0X0000000000003FFF;
    scifihit.flags    = (hitinfo      ) & 0X0000000000000003; 
    //uint16_t channelId       = (hitinfo >> 50);
    //unsigned int hitTime  = (hitinfo >> 18) & 0X00000000FFFFFFFF;
    //unsigned int fineTime = (hitinfo >> 2 ) & 0X0000000000003FFF;
    //unsigned int flag     = (hitinfo      ) & 0X0000000000000003; 
    //unsigned int fineTime = hitinfo         & aux[0]; 
    //unsigned int hitTime  = (hitinfo >> 5)  & aux[1]; 
    //unsigned int amp      = (hitinfo >> 41) & aux[2]; 
    //unsigned int ch       = (hitinfo >> 49) & aux[3]; 
    //unsigned int sticId   = (hitinfo >> 55) & aux[4]; 
    //unsigned int boardId  = (hitinfo >> 58) & aux[3]; 
    //bool flag     = hitinfo & aux[5];
    bool trigflag;

    //std::cout << std::hex << "hitdata :)  \tfineTime:  " << fineTime 
    //  << "\thitTime: "<< hitTime << "\tamp: " << amp << "\tch: " << ch << "\tsticId: "
    //  << sticId << "\tboardId: " << boardId << std::endl;

    if (scifihit.ch > 12289) continue;
    //if (scifihit.ch < 12289){
      trigflag = 0;
      uint16_t module = int(scifihit.ch/1536)+1; // range from 1 - 8
      uint16_t channelId = int(scifihit.ch/module);
      uint16_t boardId = int(scifihit.ch/512);
      new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, scifihit.time*25, scifihit.finetime*32./680, scifihit.ch, boardId, module, scifihit.flags);
      fNHits++;
    //}
    //if (scifihit.ch > 16000){
    //  trigflag = 1;
    //  uint16_t boardId = scifihit.ch - 16000;
    //  uint16_t module = boardId/3;
    //  if (module > 7) continue;
    //  new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, scifihit.time*25, scifihit.finetime*32./680,0, boardId, module, scifihit.flags, trigflag);
    //  fNHits++;
    //}
      //new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitTime*25, fineTime*32./680, amp, ch, boardId, sticId, flag);
      //fNHits++;
  }

  //fNHitsTotal += fNHits;
  return kTRUE;
}

// Reset: Public method
void SciFiUnpack::Reset()
{
  fRawData->Clear();
  fNHits = 0;
}

ClassImp(SciFiUnpack)
