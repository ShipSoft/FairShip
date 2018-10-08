#include <cassert>
#include <unordered_map>
#include <iostream>

// ROOT headers
#include "TClonesArray.h"
#include "ROOT/TSeq.hxx"

// Fair headers
#include "FairRootManager.h"
#include "FairRunOnline.h"
#include "FairLogger.h"

// SHiP headers
#include "DriftTubeUnpack.h"
#include "MufluxSpectrometerHit.h"
#include "ScintillatorHit.h"
#include "ShipOnlineDataFormat.h"

using DriftTubes::ChannelId;

// DriftTubeUnpack: Constructor
DriftTubeUnpack::DriftTubeUnpack(Short_t type, Short_t subType, Short_t procId, Short_t subCrate, Short_t control)
   : ShipUnpack(type, subType, procId, subCrate, control), fRawTubes(new TClonesArray("MufluxSpectrometerHit")),
     fRawScintillator(new TClonesArray("ScintillatorHit")), fNHitsTubes(0), fNHitsScintillator(0), fNHitsTotalTubes(0),
     fNHitsTotalScintillator(0), fPartitionId(0x0C00)
{
}

// Virtual DriftTubeUnpack: Public method
DriftTubeUnpack::~DriftTubeUnpack()
{
   LOG(INFO) << "DriftTubeUnpack: Delete instance" << FairLogger::endl;
   delete fRawTubes;
   delete fRawScintillator;
}

// Init: Public method
Bool_t DriftTubeUnpack::Init()
{
   Register();
   return kTRUE;
}

// Register: Protected method
void DriftTubeUnpack::Register()
{
   LOG(INFO) << "DriftTubeUnpack : Registering..." << FairLogger::endl;
   auto fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("Digi_MufluxSpectrometerHits", "DriftTubes", fRawTubes, kTRUE);
   fMan->Register("Digi_ScintillatorHits", "DriftTubes", fRawScintillator, kTRUE);
}

// DoUnpack: Public method
Bool_t DriftTubeUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(DEBUG) << "DriftTubeUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   assert(df->header.size == size);
   switch (df->header.frameTime){
      case SoS:
         LOG(DEBUG) << "DriftTubeUnpacker: SoS frame." << FairLogger::endl;
            for (int i = 0; i < size; i++) {
               if (i % 4 == 0) {
                  std::cout << ' ';
               } else if (i % 16 == 0) {
                  std::cout << '\n';
               }
               std::cout << std::hex << +data[i] << std::dec;
            }
            std::cout << std::endl;
         return kTRUE;
      case EoS:
         LOG(DEBUG) << "DriftTubeUnpacker: EoS frame." << FairLogger::endl;
         return kTRUE;
      default:
         break;
   }
   LOG(DEBUG) << "Sequential trigger number " << df->header.timeExtent << FairLogger::endl;
   auto nhits = df->getHitCount();
   int skipped = 0;
   int trigger = 0;
   std::vector<RawDataHit> hits(df->hits, df->hits + nhits);
   std::unordered_map<uint16_t, uint16_t> channels;
   std::unordered_map<int, uint16_t> triggerTime;
   uint16_t master_trigger_time = 0;
   std::vector<std::pair<int,uint16_t>> trigger_times;
   for (auto &&hit : hits) {
      if (hit.channelId >= 0x1000) {
         // trailing edge
         skipped++;
         continue;
      }
      auto channel = reinterpret_cast<ChannelId *>(&(hit.channelId));
      auto detectorId = channel->GetDetectorId();
      if (!detectorId) {
         trigger++;
         triggerTime[channel->TDC] = hit.hitTime;
         trigger_times.push_back(std::make_pair(int(channel->TDC), hit.hitTime));
         skipped++;
      } else if (detectorId == 1) {
         master_trigger_time = hit.hitTime;
         skipped++;
      } else if (detectorId == -1) {
         // beam counter
         skipped++;
      } else if (channels.find(hit.channelId) != channels.end()) {
         channels[hit.channelId] = std::min(hit.hitTime, channels[hit.channelId]);
         skipped++;
      } else {
         channels[hit.channelId] = hit.hitTime;
      }
   }
   uint16_t delay = 2000;
   if (!triggerTime[4]) {
      LOG(WARNING) << "No trigger in TDC 4, guessing delay" << FairLogger::endl;
   } else if (master_trigger_time == 0){
      LOG(WARNING) << "No master trigger, guessing delay" << FairLogger::endl;
   } else {
      delay = triggerTime[4] - master_trigger_time;
   }
   for (auto &&channel_and_time : channels) {
      auto channel = reinterpret_cast<const ChannelId *>(&(channel_and_time.first));
      uint16_t raw_time = channel_and_time.second;
      uint16_t trigger_time;
      try {
         trigger_time = triggerTime.at(channel->TDC);
      } catch (const std::out_of_range &e) {
         auto detectorId = channel->GetDetectorId();
         LOG(WARNING) << e.what() << "\t TDC " << channel->TDC << "\t Detector ID " << detectorId << "\t Channel "
                      << channel_and_time.first << "\t Sequential trigger number " << df->header.timeExtent
                      << FairLogger::endl;
         skipped++;
         continue;
      }
      LOG(DEBUG) << "Sequential trigger number " << df->header.timeExtent << FairLogger::endl;
      Float_t time = 0.098 * (delay - trigger_time + raw_time); // conversion to ns and jitter correction
      auto detectorId = channel->GetDetectorId();
      if (detectorId == 6 || detectorId == 7) {
         // Trigger scintillator
         new ((*fRawScintillator)[fNHitsScintillator]) ScintillatorHit(detectorId, time);
         fNHitsScintillator++;
      } else {
         new ((*fRawTubes)[fNHitsTubes]) MufluxSpectrometerHit(detectorId, time, df->header.flags);
         fNHitsTubes++;
      }
   }

   if (trigger != 5) {
      LOG(INFO) << trigger << " triggers." << FairLogger::endl;
      for (auto&& i : trigger_times) {
         LOG(INFO) << i.first << '\t' <<  i.second << FairLogger::endl;
      }
   } else {
      LOG(DEBUG) << trigger << " triggers." << FairLogger::endl;
   }

   assert(fRawTubes->GetEntries() + fRawScintillator->GetEntries() + skipped == nhits);
   assert(nhits == fNHitsTubes + fNHitsScintillator + skipped);

   fNHitsTotalTubes += fNHitsTubes;
   fNHitsTotalScintillator += fNHitsScintillator;

   return kTRUE;
}

// Reset: Public method
void DriftTubeUnpack::Reset()
{
   LOG(DEBUG) << "DriftTubeUnpack : Clearing Data Structure" << FairLogger::endl;
   fRawTubes->Clear();
   fRawScintillator->Clear();
   fNHitsTubes = 0;
   fNHitsScintillator = 0;
}

ClassImp(DriftTubeUnpack)
