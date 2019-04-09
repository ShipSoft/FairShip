#include <cassert>

// ROOT headers
#include "TClonesArray.h"

// Fair headers
#include "FairRootManager.h"
#include "FairRunOnline.h"
#include "FairLogger.h"

// SHiP headers
#include "RPCUnpack.h"
#include "MuonTaggerHit.h"
#include "ShipOnlineDataFormat.h"

struct RawHit {
   uint16_t ncrate : 8;
   uint16_t nboard : 8;
   uint16_t hitTime;
   uint8_t pattern[8];
};

enum Direction { horizontal = 0, vertical = 1 };

int GetId(int ncrate, int nboard, int channel)
{
   assert(ncrate == 16 || ncrate == 18);
   assert(nboard > 0 && nboard < 16);
   int station;
   int nboardofstation;
   switch (ncrate) {
   case 16:
      station = (nboard < 6) ? 1 : 2;
      nboardofstation = nboard - (station - 1) * 5;
      break;
   case 18:
      station = (nboard < 6) ? 3 : (nboard < 11) ? 4 : 5;
      nboardofstation = nboard - (station - 3) * 5;
      break;
   }
   int direction = (nboardofstation < 4) ? vertical : horizontal;
   int strip = direction == vertical
                  ? channel - 3
                  : (channel < 16) ? 10 - channel
                                   : (channel < 32) ? 42 - channel : (channel < 48) ? 74 - channel : 106 - channel;
   strip += (nboardofstation - (direction == vertical ? 1 : 4)) * 64;
   LOG(DEBUG) << ncrate << '\t' << nboard << '\t' << channel << '\t' << station << '\t' << strip << '\t'
              << (direction == vertical ? 'V' : 'H') << FairLogger::endl;
   return 10000 * station + 1000 * direction + strip;
}

// RPCUnpack: Constructor
RPCUnpack::RPCUnpack() : fRawData(new TClonesArray("MuonTaggerHit")), fNHits(0), fNHitsTotal(0), fPartitionId(0x0B00) {}

// Virtual RPCUnpack: Public method
RPCUnpack::~RPCUnpack() = default;

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
   fMan->Register("Digi_MuonTaggerHits", "RPCs", fRawData.get(), kTRUE);
}

// DoUnpack: Public method
Bool_t RPCUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(DEBUG) << "RPCUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;

   auto df = reinterpret_cast<DataFrame *>(data);
   switch (df->header.frameTime) {
   case SoS: LOG(INFO) << "RPCUnpack: SoS frame." << FairLogger::endl; return kTRUE;
   case EoS: LOG(INFO) << "RPCUnpack: EoS frame." << FairLogger::endl; return kTRUE;
   default: break;
   }
   assert(df->header.size == size);
   auto nhits = (size - sizeof(DataFrame)) / 12;
   static_assert(sizeof(RawHit) == 12, "Padding is off");
   int skipped = 0;
   auto hits = reinterpret_cast<unsigned char *>(df->hits);
   const int BYTES_PER_HITPATTERN = 8;
   const int BYTES_PER_RECORD = 12;
   for (int i = 0; i < nhits; i++) {
      auto hit = hits + i * BYTES_PER_RECORD;
      auto crate = (unsigned int)hit[0];
      auto board = (unsigned int)hit[1];
      for (int k = 1; k <= BYTES_PER_HITPATTERN; k++) {
         auto index = k + 3;

         auto bitMask = 0x1;
         for (int j = 0; j < 8; j++) {
            if (hit[index] & bitMask) {
               auto channel = (BYTES_PER_HITPATTERN - k) * 8 + j;
               if ((crate == 16 && (board == 5 || board == 10) && channel >= 48 && channel <= 53) ||
                   (crate == 16 && (board == 3 || board == 8) && channel >= 60 && channel <= 63) ||
                   (crate == 16 && (board == 4 || board == 9) && channel >= 10 && channel <= 15) ||
                   (crate == 16 && (board == 1 || board == 6) && channel >= 0 && channel <= 3) ||
                   (crate == 18 && (board == 5 || board == 10 || board == 15) && channel >= 48 && channel <= 53) ||
                   (crate == 18 && (board == 3 || board == 8 || board == 13) && channel >= 60 && channel <= 63) ||
                   (crate == 18 && (board == 4 || board == 9 || board == 14) && channel >= 10 && channel <= 15) ||
                   (crate == 18 && (board == 1 || board == 6 || board == 11) && channel >= 0 && channel <= 3)) {
                  skipped++;
                  continue;
               }
               new ((*fRawData)[fNHits])
                  MuonTaggerHit(GetId(crate, board, channel), Float_t(df->header.frameTime) * 25);
               fNHits++;
            }
            bitMask <<= 1;
         }
      }
   }

   if (skipped) {
      LOG(WARNING) << "Skipped " << skipped << " hits on unconnected channels (probably noise)." << FairLogger::endl;
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
