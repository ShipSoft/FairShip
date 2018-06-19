#include <cassert>

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
   : FairUnpack(type, subType, procId, subCrate, control), fRawTubes(new TClonesArray("MufluxSpectrometerHit")),
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
   //  LOG(DEBUG) << "Registering" << FairLogger::endl;
   LOG(INFO) << "DriftTubeUnpack : Registering..." << FairLogger::endl;
   FairRootManager *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("MufluxSpectrometerHit", "DriftTubes", fRawTubes, kTRUE);
   fMan->Register("ScintillatorHit", "DriftTubes", fRawScintillator, kTRUE);
}

// DoUnpack: Public method
Bool_t DriftTubeUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(DEBUG) << "DriftTubeUnpack : Unpacking frame... size = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   assert(df->header.size == size);
   auto nhits = df->getHitCount();
   int skipped = 0;
   int trigger = 0;
   std::vector<RawDataHit> hits(df->hits, df->hits + nhits);
   for (auto &&hit : hits) {
      // TODO read array into searchable container?
      auto channel = reinterpret_cast<ChannelId *>(&(hit.channelId));
      Float_t time = hit.hitTime * 0.098; // Convert time to ns
      auto detectorId = channel->GetDetectorId();
      if (!detectorId) {
         // TODO use trigger for time adjustment, don't save it as a hit
         trigger++;
         skipped++;
      } else if (detectorId == 6 || detectorId == 7) {
         // Trigger scintillator
         new ((*fRawScintillator)[fNHitsScintillator]) ScintillatorHit(detectorId, time);
         fNHitsScintillator++;
      } else if (detectorId == -1) {
         // beam counter
         skipped++;
      } else {
         new ((*fRawTubes)[fNHitsTubes]) MufluxSpectrometerHit(detectorId, time);
         fNHitsTubes++;
      }
   }

   LOG(INFO) << trigger << FairLogger::endl;

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
