#include <cassert>
#include <unordered_map>
#include <iostream>
#include <bitset>

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
DriftTubeUnpack::DriftTubeUnpack()
   : fRawTubes(new TClonesArray("MufluxSpectrometerHit")), fRawScintillator(new TClonesArray("ScintillatorHit")),
     fRawBeamCounter(new TClonesArray("ScintillatorHit")), fRawMasterTrigger(new TClonesArray("ScintillatorHit")),
     fRawTriggers(new TClonesArray("ScintillatorHit")),  fPartitionId(0x0C00)
{
}

// Virtual DriftTubeUnpack: Public method
DriftTubeUnpack::~DriftTubeUnpack() = default;

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
   fMan->Register("Digi_MufluxSpectrometerHits", "DriftTubes", fRawTubes.get(), kTRUE);
   fMan->Register("Digi_Scintillators", "DriftTubes", fRawScintillator.get(), kTRUE);
   fMan->Register("Digi_BeamCounters", "DriftTubes", fRawBeamCounter.get(), kTRUE);
   fMan->Register("Digi_MasterTrigger", "DriftTubes", fRawMasterTrigger.get(), kTRUE);
   fMan->Register("Digi_Triggers", "DriftTubes", fRawTriggers.get(), kTRUE);
}

// DoUnpack: Public method
Bool_t DriftTubeUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(DEBUG) << "DriftTubeUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   assert(df->header.size == size);
   switch (df->header.frameTime) {
   case SoS:
      LOG(DEBUG) << "DriftTubeUnpacker: SoS frame." << FairLogger::endl;
      for (auto i : ROOT::MakeSeq(size)) {
         if (i % 4 == 0) {
            std::cout << ' ';
         } else if (i % 16 == 0) {
            std::cout << '\n';
         }
         std::cout << std::hex << +data[i] << std::dec;
      }
      std::cout << std::endl;
      return kTRUE;
   case EoS: LOG(DEBUG) << "DriftTubeUnpacker: EoS frame." << FairLogger::endl; return kTRUE;
   default: break;
   }
   LOG(DEBUG) << "Sequential trigger number " << df->header.timeExtent << FairLogger::endl;
   auto nhits = df->getHitCount();
   int nhitsTubes = 0;
   int nhitsScintillator = 0;
   int nhitsBeamCounter = 0;
   int nhitsMasterTrigger = 0;
   int nhitsTriggers = 0;
   auto flags = df->header.flags;
   int skipped = 0;
   int trigger = 0;
   int expected_triggers = 5;
   if ((flags & DriftTubes::All_OK) == DriftTubes::All_OK) {
      LOG(DEBUG) << "All TDCs are OK" << FairLogger::endl;
   } else {
      LOG(DEBUG) << "Not all TDCs are OK:" << std::bitset<16>(flags) << FairLogger::endl;
      for (auto i : ROOT::MakeSeq(5)) {
         if ((flags & 1 << (i + 1)) == 1 << (i + 1)) {
            expected_triggers--;
            LOG(WARNING) << "TDC " << i << " NOT OK" << FairLogger::endl;
         } else {
            LOG(DEBUG) << "TDC " << i << " OK" << FairLogger::endl;
         }
      }
   }
   std::vector<RawDataHit> hits(df->hits, df->hits + nhits);
   std::unordered_map<uint16_t, uint16_t> channels;
   std::unordered_map<int, uint16_t> triggerTime;
   uint16_t master_trigger_time = 0;
   std::vector<std::pair<int, uint16_t>> trigger_times;
   for (auto &&hit : hits) {
      auto channel = reinterpret_cast<ChannelId *>(&(hit.channelId));
      auto TDC = channel->TDC;
      auto detectorId = channel->GetDetectorId();
      if (!detectorId) {
         if (channel->edge == 0) {
            trigger++;
            triggerTime[TDC] =
               (triggerTime.find(TDC) != triggerTime.end()) ? std::min(hit.hitTime, triggerTime[TDC]) : hit.hitTime;
            trigger_times.emplace_back(TDC, hit.hitTime);
         }
         new ((*fRawTriggers)[nhitsTriggers])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit.hitTime), flags, hit.channelId);
         nhitsTriggers++;
      } else if (detectorId == 1) {
         if (channel->edge == 0) {
            master_trigger_time = hit.hitTime;
         }
         new ((*fRawMasterTrigger)[nhitsMasterTrigger])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit.hitTime), flags, hit.channelId);
         nhitsMasterTrigger++;
      } else if (detectorId == -1) {
         // beam counter
         new ((*fRawBeamCounter)[nhitsBeamCounter])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit.hitTime), flags, hit.channelId);
         nhitsBeamCounter++;
      } else if (detectorId == 6 || detectorId == 7) {
         // beam counter
         new ((*fRawScintillator)[nhitsScintillator])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit.hitTime), flags, hit.channelId);
         nhitsScintillator++;
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
   } else if (master_trigger_time == 0) {
      LOG(WARNING) << "No master trigger, guessing delay" << FairLogger::endl;
   } else {
      delay = triggerTime[4] - master_trigger_time;
   }
   for (auto &&channel_and_time : channels) {
      uint16_t raw_chan = channel_and_time.first;
      uint16_t raw_time = channel_and_time.second;
      auto channel = reinterpret_cast<const ChannelId *>(&raw_chan);
      auto TDC = channel->TDC;
      uint16_t trigger_time;
      try {
         trigger_time = triggerTime.at(TDC);
      } catch (const std::out_of_range &e) {
         auto detectorId = channel->GetDetectorId();
         LOG(WARNING) << e.what() << "\t TDC " << TDC << "\t Detector ID " << detectorId << "\t Channel "
                      << channel_and_time.first << "\t Sequential trigger number " << df->header.timeExtent
                      << FairLogger::endl;
         skipped++;
         continue;
      }
      LOG(DEBUG) << "Sequential trigger number " << df->header.timeExtent << FairLogger::endl;
      Float_t time = 0.098 * (delay - trigger_time + raw_time); // conversion to ns and jitter correction
      auto detectorId = channel->GetDetectorId();
      new ((*fRawTubes)[nhitsTubes]) MufluxSpectrometerHit(detectorId, time, flags, raw_chan);
      nhitsTubes++;
   }

   if (trigger < expected_triggers) {
      LOG(INFO) << trigger << " triggers." << FairLogger::endl;
      for (auto &&i : trigger_times) {
         LOG(INFO) << i.first << '\t' << i.second << FairLogger::endl;
      }
   } else {
      LOG(DEBUG) << trigger << " triggers." << FairLogger::endl;
   }

   if (nhits != nhitsTubes + nhitsScintillator + nhitsBeamCounter + nhitsMasterTrigger + nhitsTriggers + skipped) {
      LOG(WARNING) << "Number of Entries in containers and header disagree!" << FairLogger::endl;
   }

   return kTRUE;
}

// Reset: Public method
void DriftTubeUnpack::Reset()
{
   LOG(DEBUG) << "DriftTubeUnpack : Clearing Data Structure" << FairLogger::endl;
   fRawTubes->Clear();
   fRawScintillator->Clear();
   fRawBeamCounter->Clear();
   fRawMasterTrigger->Clear();
   fRawTriggers->Clear();
}

ClassImp(DriftTubeUnpack)
