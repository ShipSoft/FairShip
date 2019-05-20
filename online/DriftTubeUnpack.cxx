#include <cassert>
#include <unordered_map>
#include <bitset>
#include <algorithm>
#include <set>
#include <tuple>

// ROOT headers
#include "ROOT/TSeq.hxx"
#include "ROOT/RVec.hxx"

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
DriftTubeUnpack::DriftTubeUnpack() = default;

DriftTubeUnpack::DriftTubeUnpack(bool charm) : fCharm(charm) {}

// Virtual DriftTubeUnpack: Public method
DriftTubeUnpack::~DriftTubeUnpack() = default;

// Init: Public method
Bool_t DriftTubeUnpack::Init()
{
   LOG(INFO) << "DriftTubeUnpack : Initialising in " << (fCharm ? "charm" : "muon flux") << " mode."
             << FairLogger::endl;
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
   fMan->Register("Digi_LateMufluxSpectrometerHits", "DriftTubes", fRawLateTubes.get(), kTRUE);
   if (!fCharm) {
      // Scintillator was removed for charm
      fMan->Register("Digi_Scintillators", "DriftTubes", fRawScintillator.get(), kTRUE);
   }
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
   case SoS: LOG(DEBUG) << "DriftTubeUnpacker: SoS frame." << FairLogger::endl; return kTRUE;
   case EoS: LOG(DEBUG) << "DriftTubeUnpacker: EoS frame." << FairLogger::endl; return kTRUE;
   default: break;
   }
   LOG(DEBUG) << "Sequential trigger number " << df->header.timeExtent << FairLogger::endl;
   auto nhits = df->getHitCount();
   int nhitsTubes = 0;
   int nhitsLateTubes = 0;
   int nhitsScintillator = 0;
   int nhitsBeamCounter = 0;
   int nhitsMasterTrigger = 0;
   int nhitsTriggers = 0;
   auto flags = df->header.flags;
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
   ROOT::VecOps::RVec<RawDataHit> hits(df->hits, df->hits + nhits);
   ROOT::VecOps::RVec<RawDataHit> leading, trailing;
   int n_matched = 0;
   int n_unmatched = 0;
   std::set<uint16_t> channels;
   for (auto &&hit : hits) {
      channels.emplace(hit.channelId % 0x1000);
      (hit.channelId < 0x1000 ? leading : trailing).emplace_back(hit);
   }
   assert(leading.size() + trailing.size() == hits.size());
   LOG(DEBUG) << leading.size() << '\t' << trailing.size() << '\t' << hits.size();
   const int n_leading = leading.size();
   auto compare_hit_time = [](const RawDataHit &a, const RawDataHit &b) { return a.hitTime < b.hitTime; };
   std::sort(leading.begin(), leading.end(), compare_hit_time);
   std::sort(trailing.begin(), trailing.end(), compare_hit_time);
   std::unordered_map<uint16_t, ROOT::VecOps::RVec<RawDataHit>> channel_leading;
   for (auto &&hit : leading) {
      assert(hit.channelId < 0x1000);
      channel_leading[hit.channelId % 0x1000].emplace_back(hit);
   }
   std::unordered_map<uint16_t, ROOT::VecOps::RVec<RawDataHit>> channel_trailing;
   for (auto &&hit : trailing) {
      assert(hit.channelId >= 0x1000);
      channel_trailing[hit.channelId % 0x1000].emplace_back(hit);
   }
   ROOT::VecOps::RVec<std::tuple<uint16_t, uint16_t, Float_t, bool, bool>> matches;
   for (auto &&channel : channels) {
      bool first = true;
      LOG(DEBUG) << "Channel: " << channel;
      assert(channel < 0x1000);
      auto leading_hits = channel_leading[channel];
      auto trailing_hits = channel_trailing[channel];
      auto difference = int(leading_hits.size() - trailing_hits.size());
      if (difference != 0) {
         LOG(DEBUG) << "Difference between leading/trailing edges: " << difference;
      }
      for (int i = 0, j = 0; i < leading_hits.size(); i++) {
         LOG(DEBUG) << "i=" << i << "\tj=" << j;
         LOG(DEBUG) << "leading_hits.size()=" << leading_hits.size()
                    << "\ttrailing_hits.size()=" << trailing_hits.size();
         assert(i < leading_hits.size());
         if (j < trailing_hits.size() && leading_hits.at(i).hitTime < trailing_hits.at(j).hitTime &&
             (i + 1 >= leading_hits.size() || trailing_hits.at(j).hitTime < leading_hits.at(i + 1).hitTime)) {
            // Successful match
            LOG(DEBUG) << "Successful match on channel " << channel;
            uint16_t time = leading_hits.at(i).hitTime;
            Float_t time_over_threshold = 0.098 * (trailing_hits.at(j).hitTime - leading_hits.at(i).hitTime);
            matches.emplace_back(channel, time, time_over_threshold, first, true);
            n_matched++;
            first = false;
            j++;
         } else if (j < trailing_hits.size() && leading_hits.at(i).hitTime > trailing_hits.at(j).hitTime &&
                    (j + 1) < trailing_hits.size()) {
            // No match for leading edge
            // Try again with next j, same i
            LOG(DEBUG) << "Try again for hit on channel " << channel;
            i--;
            j++;
         } else {
            LOG(DEBUG) << "No match found for hit on channel " << channel;
            // No match possible, save unmatched hit
            uint16_t time = leading_hits.at(i).hitTime;
            Float_t time_over_threshold = 167.2; // Estimated from data
            matches.emplace_back(channel, time, time_over_threshold, first, false);
            first = false;
            n_unmatched++;
         }
      }
   }
   assert(n_matched + n_unmatched == n_leading);
   LOG(DEBUG) << "Successfully matched " << n_matched << "/" << n_leading << "(" << hits.size() << " hits)";

   std::unordered_map<int, uint16_t> trigger_times;
   ROOT::VecOps::RVec<std::tuple<uint16_t, uint16_t, Float_t, bool, uint16_t>> drifttube_hits;
   uint16_t master_trigger_time = 0;
   for (auto &&match : matches) {
      uint16_t channel, hit_time;
      Float_t time_over_threshold;
      bool first, matched;
      std::tie(channel, hit_time, time_over_threshold, first, matched) = match;
      auto hit_flags = matched ? flags : flags | DriftTubes::NoWidth;
      auto id = *(reinterpret_cast<ChannelId *>(&channel));
      auto detectorId = fCharm ? id.GetDetectorIdCharm() : id.GetDetectorId();
      auto TDC = id.TDC;
      if (detectorId == 0) {
         // Trigger
         trigger++;
         if (trigger_times.find(TDC) != trigger_times.end()) {
            LOG(DEBUG) << "Found time " << trigger_times[TDC] << " for TDC " << TDC << FairLogger::endl;
            trigger_times[TDC] = std::min(hit_time, trigger_times[TDC]);
         } else {
            LOG(DEBUG) << "Inserting new time " << hit_time << FairLogger::endl;
            trigger_times[TDC] = hit_time;
         }
         LOG(DEBUG) << TDC << '\t' << hit_time << '\t' << trigger_times[TDC] << FairLogger::endl;
         new ((*fRawTriggers)[nhitsTriggers])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit_time), time_over_threshold, hit_flags, channel);
         nhitsTriggers++;
      } else if (detectorId == -2) {
         // Blacklisted channel
         continue;
      } else if (detectorId == 1) {
         // Master trigger
         //
         // Use the earliest if there are several
         if (nhitsMasterTrigger == 0 || hit_time < master_trigger_time) {
            master_trigger_time = hit_time;
         }
         new ((*fRawMasterTrigger)[nhitsMasterTrigger])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit_time), time_over_threshold, hit_flags, channel);
         nhitsMasterTrigger++;
      } else if (detectorId == -1) {
         // beam counter
         new ((*fRawBeamCounter)[nhitsBeamCounter])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit_time), time_over_threshold, hit_flags, channel);
         nhitsBeamCounter++;
      } else if (detectorId == 6 || detectorId == 7) {
         // trigger scintillator
         if (fCharm) {
            LOG(ERROR) << "Scintillator hit found! There should not be any in the charmxsec measurement!"
                       << FairLogger::endl;
         }
         continue;
         new ((*fRawScintillator)[nhitsScintillator])
            ScintillatorHit(detectorId, 0.098 * Float_t(hit_time), time_over_threshold, hit_flags, channel);
         nhitsScintillator++;
      } else {
         drifttube_hits.emplace_back(channel, hit_time, time_over_threshold, first, hit_flags);
      }
   }

   int32_t delay = 13500; // Best guess based on data
   if (!trigger_times[4]) {
      LOG(WARNING) << "No trigger in TDC 4, guessing delay" << FairLogger::endl;
      flags |= DriftTubes::NoDelay;
   } else if (master_trigger_time == 0) {
      LOG(WARNING) << "No master trigger, guessing delay" << FairLogger::endl;
      flags |= DriftTubes::NoDelay;
   } else {
      delay = trigger_times[4] - master_trigger_time;
      LOG(DEBUG) << "Delay [ns]:";
      LOG(DEBUG) << 0.098 * delay << " = " << 0.098 * trigger_times[4] << " - " << 0.098 * master_trigger_time;
   }

   for (auto &&hit : drifttube_hits) {
      uint16_t channel, raw_time, hit_flags;
      Float_t time_over_threshold;
      bool first;
      std::tie(channel, raw_time, time_over_threshold, first, hit_flags) = hit;
      hit_flags |= flags;
      auto id = *(reinterpret_cast<ChannelId *>(&channel));
      auto detectorId = fCharm ? id.GetDetectorIdCharm() : id.GetDetectorId();
      auto TDC = id.TDC;
      Float_t time;
      try {
         auto trigger_time = trigger_times.at(TDC);
         time = 0.098 * (delay - trigger_time + raw_time);
      } catch (const std::out_of_range &e) {
         LOG(WARNING) << e.what() << "\t TDC " << TDC << "\t Detector ID " << detectorId << "\t Channel " << channel
                      << "\t Sequential trigger number " << df->header.timeExtent << FairLogger::endl;
         time = 0.098 * raw_time;
         hit_flags |= DriftTubes::NoTrigger;
      }
      if (time > 4000) {
         LOG(WARNING) << "Late event found with time [ns]:";
         LOG(WARNING) << time << " = " << 0.098 * delay << " - " << 0.098 * (delay + raw_time) - time << " - "
                      << 0.098 * raw_time;
      }

      new ((*(first ? fRawTubes : fRawLateTubes))[first ? nhitsTubes : nhitsLateTubes])
         MufluxSpectrometerHit(detectorId, time, time_over_threshold, hit_flags, channel);
      (first ? nhitsTubes : nhitsLateTubes)++;
   }

   if (trigger < expected_triggers) {
      LOG(INFO) << trigger << " triggers." << FairLogger::endl;
   } else {
      LOG(DEBUG) << trigger << " triggers." << FairLogger::endl;
   }

   return kTRUE;
}

// Reset: Public method
void DriftTubeUnpack::Reset()
{
   LOG(DEBUG) << "DriftTubeUnpack : Clearing Data Structure" << FairLogger::endl;
   fRawTubes->Clear();
   fRawLateTubes->Clear();
   fRawScintillator->Clear();
   fRawBeamCounter->Clear();
   fRawMasterTrigger->Clear();
   fRawTriggers->Clear();
}

ClassImp(DriftTubeUnpack)
