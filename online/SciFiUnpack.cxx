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

//struct HitData {
//   uint64_t hitword;
//};

struct HitData{
  uint64_t flags    : 2 ; // flags
  uint64_t finetime : 16; // fine time
  uint64_t time     : 32; // time
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
};
struct ChannelId{
  uint16_t channel  : 11; // 0 - 1536
  uint16_t board    : 5 ; // 0 - 23
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
  int module;
  int channel_number;
  int flag;
  UInt_t time;
  UShort_t finetime;
  uint64_t hitword;
  std::ofstream fout;
  fout.open("raw-to-hex_scifiunpack.csv",  std::ofstream::out | std::ofstream::app);

//  TFile f("converted_v1.root","RECREATE");
//  TTree *tree = new TTree("scifihits","Converted hits");
//  tree->Branch("channel_number",&channel_number,"channel_number/I");
//  tree->Branch("time",&time,"time/i");
//  tree->Branch("finetime",&finetime,"finetime/s");
//  tree->Branch("module",&module,"module/I");
//  tree->Branch("flag",&flag,"flag/I");  

  LOG(INFO) << "SciFiUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

  auto df = reinterpret_cast<DataFrame *>(data);
  switch (df->header.frameTime) {
    case SoS: LOG(INFO) << "SciFiUnpack: SoS frame." << FairLogger::endl; return kTRUE;
    case EoS: LOG(INFO) << "SciFiUnpack: EoS frame." << FairLogger::endl; return kTRUE;
    default: break;
  }
  int i =0;
  assert(df->header.size == size);
  auto nhits = df->getHitCount();
  std::vector<RawDataHit> hits(df->hits, df->hits + nhits);
  //std::cout << df->header.size << "  " << size << "  " << nhits << std::endl;
  for (auto &&hit : hits) {
    auto hitData = reinterpret_cast<HitData *>(&(hit));
    //auto channelId = reinterpret_cast<ChannelId *>(&(hit.channelId))
    //   //auto channelId = reinterpret_cast<ChannelId *>(&(hit.channelId));
    //   //auto detectorId = 1000000 * hitData->moduleID + 1000 * channelId->row + channelId->column;
    //auto a = hitData->ch;
    //auto b = hitData->time;
    //auto c = hitData->finetime;
    //auto d = hitData->flags;
    //fout << std::hex << hitData->ch << std::endl;
    fout << hitData->ch << "\t" << hitData->time << "\t" << hitData->finetime << "\t" << hitData->flags << std::endl;
    //if (i==25) {
    //  uint64_t hitdata=(((uint64_t)a)<<50 | ((uint64_t)b)<<18 |((uint64_t)c)<<2 | ((uint64_t)d));
    //  std::cout << std::hex << hitdata << std::endl;
    //  std::cout << std::hex << a << " " << b << " " << c << " " << d << std::endl;
    //}
    //i++;
    //bool trigflag;
    //if (hitData->ch < 12289) trigflag=0;
    //if (hitData->ch > 16000) trigflag=1;

//    if (hitData->ch >= 16000) {module = hitData->ch - 16000; channel_number = hitData->ch; flag = 0;}
//    else if (hitData->ch < 12289) {module = hitData->ch/1536+1; channel_number = hitData->ch; flag = 1;}
//    else {module = 0; channel_number = hitData->ch; flag=2;}
//    time=hitData->time*25;
//    finetime=hitData->finetime*32./680;
//
//    tree->Fill();

    //auto detectorId = hitData->ch/1536+1;
  //  auto module = hitData->ch / 1536 + 1;;
  //  auto boardId = hitData->ch/512;
   bool trigflag;
 if (hitData->ch <= 12289 & hitData->ch > 0){
  //   //boardId  = hitData->ch/512;
  //   //module   = hitData->ch / 1536 + 1;
     trigflag = 0;
  //   //channel  = hitData->ch/1536;
  }
   else {
  //   boardId = hitData->ch - 16000;
  //   module = boardId/3;
     trigflag = 1;
  //   //channel = 0;
  }
  //if(boardId > 26)  std::cout << trigflag << "\t" << boardId << "\t" << module << std::endl;

   //new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitData->time, hitData->finetime, hitData->ch, boardId, module, trigflag, hitData->flags);
   new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitData->time, hitData->finetime, hitData->ch, 0, 0, trigflag, hitData->flags);
    //else new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitData->time*25, hitData->finetime*32./680,0, (hitData->ch-16000), (hitData->ch - 16000)/3, hitData->flags);
    //new ((*fRawData)[fNHits]) SciFiHit(detectorId,channel);
    //new ((*fRawData)[fNHits]) SciFiHit(0x0900,0, hitData->time*25, hitData->finetime*32./680, channel, boardId, module, hitData->flags);
    //new ((*fRawData)[fNHits]) SciFiHit(detectorId,0, hitData->time * 25, hitData->finetime * 32./680, hitData->ch, boardId, 0, trigflag);
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
  //f.Write();
  //fout.close();
  return kTRUE;
}

// Reset: Public method
void SciFiUnpack::Reset()
{
  fRawData->Clear();
  fNHits = 0;
}

ClassImp(SciFiUnpack)
