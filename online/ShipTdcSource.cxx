#include "ShipTdcSource.h"
#include "FairLogger.h"
#include "ShipOnlineDataFormat.h"
#include "DriftTubeUnpack.h"

ShipTdcSource::ShipTdcSource() : FairOnlineSource(), fFilename("tdcdata.bin") {}

ShipTdcSource::ShipTdcSource(std::string filename) : FairOnlineSource(), fFilename(filename) {}

ShipTdcSource::ShipTdcSource(const ShipTdcSource &source) : FairOnlineSource(source) {}

ShipTdcSource::~ShipTdcSource() {}

Bool_t ShipTdcSource::Init()
{
   fIn = new std::ifstream(fFilename, std::ios::binary);
   return kTRUE;
}

void ShipTdcSource::Close()
{
   fIn->close();
}

Int_t ShipTdcSource::UnpackEventFrame(Int_t *data, Int_t total_size)
{
   auto mf = reinterpret_cast<DataFrame *>(data);
   total_size -= sizeof(DataFrame);
   data = reinterpret_cast<Int_t *>(&(mf->hits));
   switch (mf->header.frameTime) {
   case 0xFF005C03: LOG(INFO) << "ShipTdcSource: SoS frame." << FairLogger::endl; break;
   case 0xFF005C04: LOG(INFO) << "ShipTdcSource: EoS frame." << FairLogger::endl; break;
   default: break;
   }
   while (total_size > 0) {
      auto df = reinterpret_cast<DataFrame *>(data);
      Int_t size = df->header.size;
      uint16_t partitionId = df->header.partitionId;
      LOG(INFO) << "ShipTdcSource: PartitionId " << std::hex << partitionId << std::dec << FairLogger::endl;
      if (!Unpack(data, size, partitionId)) {
         LOG(WARNING) << "ShipTdcSource: Failed to Unpack." << FairLogger::endl;
         LOG(WARNING) << "ShipTdcSource: Maybe missing unpacker for PartitionId " << std::hex << partitionId << std::dec
                      << FairLogger::endl;
         return 3;
      }
      data += size / sizeof(Int_t);
      total_size -= size;
   }
   assert(total_size == 0);
   return 0;
}

Int_t ShipTdcSource::ReadEvent(UInt_t)
{
   auto df = new (buffer) DataFrame();
   if (fIn->read(reinterpret_cast<char *>(df), sizeof(DataFrame))) {
      size_t size = df->header.size;
      uint16_t partitionId = df->header.partitionId;
      if (partitionId == 0x8000) {
         LOG(INFO) << "ShipTdcSource: Event builder meta frame." << FairLogger::endl;
         if (fIn->read(reinterpret_cast<char *>(df->hits), size - sizeof(DataFrame))) {
            return UnpackEventFrame(reinterpret_cast<Int_t *>(&buffer), size);
         }
      }
      LOG(INFO) << "ShipTdcSource: PartitionId " << std::hex << partitionId << std::dec << FairLogger::endl;
      if (fIn->read(reinterpret_cast<char *>(df->hits), size - sizeof(DataFrame))) {

         if (Unpack(reinterpret_cast<Int_t *>(&buffer), size, partitionId)) {
            return 0;
         }
         LOG(WARNING) << "ShipTdcSource: Failed to Unpack." << FairLogger::endl;
         LOG(WARNING) << "ShipTdcSource: Maybe missing unpacker for PartitionId " << std::hex << partitionId << std::dec
                      << FairLogger::endl;
         return 3;
      }
      LOG(WARNING) << "ShipTdcSource: Failed to read hits." << FairLogger::endl;
      return 2;
   }
   return 1;
   LOG(WARNING) << "ShipTdcSource: Failed to read header." << FairLogger::endl;
}

Bool_t ShipTdcSource::Unpack(Int_t *data, Int_t size, uint16_t partitionId)
{

   for (TObject *item : *fUnpackers) {
      auto unpacker = static_cast<ShipUnpack *>(item);
      if (unpacker->GetPartition() == partitionId) {
         return unpacker->DoUnpack(data, size);
      }
   }

   LOG(WARNING) << "ShipTdcSource: Failed to find suitable unpacker." << FairLogger::endl;
   return kFALSE;
}

ClassImp(ShipTdcSource)
