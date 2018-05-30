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
#include "ShipOnlineDataFormat.h"

using DriftTubes::ChannelId;

// DriftTubeUnpack: Constructor
DriftTubeUnpack::DriftTubeUnpack(Short_t type, Short_t subType, Short_t procId, Short_t subCrate, Short_t control)
   : FairUnpack(type, subType, procId, subCrate, control), fRawData(new TClonesArray("MufluxSpectrometerHit")),
     fNHits(0), fNHitsTotal(0)
{
}

// Virtual DriftTubeUnpack: Public method
DriftTubeUnpack::~DriftTubeUnpack()
{
   LOG(INFO) << "DriftTubeUnpack: Delete instance" << FairLogger::endl;
   delete fRawData;
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
   fMan->Register("MufluxSpectrometerHit", "TDC", fRawData, kTRUE);
}

// DoUnpack: Public method
Bool_t DriftTubeUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(DEBUG) << "DriftTubeUnpack : Unpacking frame... size = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   assert(df->header.size == size);
   auto nhits = df->getHitCount();
   for (int i : ROOT::MakeSeq(nhits)) {
      auto channel = reinterpret_cast<ChannelId*>(&(df->hits[i].channelId));
      Float_t time = df->hits[i].hitTime * 0.098; // Convert time to ns
      auto detectorId = channel->channel; // TODO need to convert accordingly
      new ((*fRawData)[fNHits]) MufluxSpectrometerHit(detectorId, time);
      fNHits++;
   }

   assert(fRawData->GetEntries() == nhits);
   assert(nhits == fNHits);

   fNHitsTotal += fNHits;

   return kTRUE;
}

// Reset: Public method
void DriftTubeUnpack::Reset()
{
   LOG(DEBUG) << "DriftTubeUnpack : Clearing Data Structure" << FairLogger::endl;
   fRawData->Clear();
   fNHits = 0;
}

ClassImp(DriftTubeUnpack)
