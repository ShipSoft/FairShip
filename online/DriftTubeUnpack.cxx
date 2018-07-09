#include <cassert>
#include <unordered_map>

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
   delete fRawTubes, fRawScintillator;
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
   FairRootManager *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("Digi_MufluxSpectrometerHits", "DriftTubes", fRawTubes, kTRUE);
   fMan->Register("Digi_ScintillatorHits", "DriftTubes", fRawScintillator, kTRUE);
}

// DoUnpack: Public method
Bool_t DriftTubeUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(INFO) << "DriftTubeUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   LOG(INFO) << "Sequential trigger number " << df->header.timeExtent << FairLogger::endl;
   assert(df->header.size == size);
   auto nhits = df->getHitCount();
   int skipped = 0;
   int trigger = 0;
   std::vector<RawDataHit> hits(df->hits, df->hits + nhits);
   std::unordered_map<uint16_t, uint16_t> channels;
   std::unordered_map<int, uint16_t> triggerTime;
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
      Float_t time = 0.098 * (DriftTubes::delay - trigger_time + raw_time); // conversion to ns and jitter correction
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
