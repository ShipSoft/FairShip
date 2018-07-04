#include <cassert>
#include <unordered_map>
#include <bitset>

// ROOT headers
#include "TClonesArray.h"
#include "ROOT/TSeq.hxx"

// Fair headers
#include "FairRootManager.h"
#include "FairRunOnline.h"
#include "FairLogger.h"

// SHiP headers
#include "RPCUnpack.h"
#include "MuonTaggerHit.h"
#include "ShipOnlineDataFormat.h"

using RPC::RawHit;

// RPCUnpack: Constructor
RPCUnpack::RPCUnpack(Short_t type, Short_t subType, Short_t procId, Short_t subCrate, Short_t control)
   : ShipUnpack(type, subType, procId, subCrate, control), fRawData(new TClonesArray("MuonTaggerHit")), fNHits(0),
     fNHitsTotal(0), fPartitionId(0x0B00)
{
}

// Virtual RPCUnpack: Public method
RPCUnpack::~RPCUnpack()
{
   LOG(INFO) << "RPCUnpack: Delete instance" << FairLogger::endl;
   delete fRawData;
}

// Init: Public method
Bool_t RPCUnpack::Init()
{
   Register();
   return kTRUE;
}

// Register: Protected method
void RPCUnpack::Register()
{
   LOG(INFO) << "RPCUnpack : Registering..." << FairLogger::endl;
   FairRootManager *fMan = FairRootManager::Instance();
   if (!fMan) {
      return;
   }
   fMan->Register("Digi_MuonTaggerHits", "RPCs", fRawData, kTRUE);
}

// DoUnpack: Public method
Bool_t RPCUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(INFO) << "RPCUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   assert(df->header.size == size);
   auto nhits = (size - sizeof(DataFrame)) / 12;
   int skipped = 0;
   auto hitptr = reinterpret_cast<RawHit *>(df->hits);
   std::vector<RawHit> hits(hitptr, hitptr + nhits);
   for (auto &&hit : hits) {
      std::bitset<64> hitmap(*reinterpret_cast<uint64_t *>(hit.pattern));
      LOG(INFO) << hitmap << FairLogger::endl;
      for (int channel = 0; channel < 64; channel++) {
         if (hitmap[63 - channel]) {
            LOG(INFO) << "Channel " << channel << " registered a hit" << FairLogger::endl;
            LOG(INFO) << "Detector " << hit.GetDetectorId(channel) << " registered a hit" << FairLogger::endl;
            // TODO should there always be pairs of channels (at least) per frame?
            new ((*fRawData)[fNHits]) MuonTaggerHit(hit.GetDetectorId(channel), 0);
            fNHits++;
         }
      }
   }
   fNHitsTotal += fNHits;
   return kTRUE;
}

// Reset: Public method
void RPCUnpack::Reset()
{
   LOG(DEBUG) << "RPCUnpack : Clearing Data Structure" << FairLogger::endl;
   fRawData->Clear();
   fNHits = 0;
}

ClassImp(RPCUnpack)
