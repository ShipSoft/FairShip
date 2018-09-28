#include "ShipTdcSource.h"
#include "FairLogger.h"
#include "FairEventHeader.h"
#include "ShipUnpack.h"
#include "ShipOnlineDataFormat.h"

ShipTdcSource::ShipTdcSource() : FairOnlineSource(), fFilename("tdcdata.bin") {}

ShipTdcSource::ShipTdcSource(TString filename) : FairOnlineSource(), fFilename(filename) {}

ShipTdcSource::ShipTdcSource(const ShipTdcSource &source) : FairOnlineSource(source) {}

ShipTdcSource::~ShipTdcSource() = default;

Bool_t ShipTdcSource::Init()
{
   fIn = TFile::Open(fFilename + "?filetype=raw", "read");
   return kTRUE;
}

void ShipTdcSource::Close()
{
   fIn->Close();
}

Int_t ShipTdcSource::UnpackEventFrame(Int_t *data, Int_t total_size)
{
   auto mf = reinterpret_cast<DataFrame *>(data);
   total_size -= sizeof(DataFrame);
   data = reinterpret_cast<Int_t *>(&(mf->hits));
   switch (mf->header.frameTime) {
   case SoS: LOG(DEBUG) << "ShipTdcSource: SoS frame." << FairLogger::endl; break;
   case EoS: LOG(DEBUG) << "ShipTdcSource: EoS frame." << FairLogger::endl; break;
   default: break;
   }
   while (total_size > 0) {
      auto df = reinterpret_cast<DataFrame *>(data);
      Int_t size = df->header.size;
      uint16_t partitionId = df->header.partitionId;
      LOG(DEBUG) << "ShipTdcSource: PartitionId " << std::hex << partitionId << std::dec << FairLogger::endl;
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
   if (!fIn->ReadBuffer(reinterpret_cast<char *>(df), sizeof(DataFrame))) {
      size_t size = df->header.size;
      fEventTime = df->header.frameTime;
      uint16_t partitionId = df->header.partitionId;
      if (partitionId == 0x8000) {
         LOG(DEBUG) << "ShipTdcSource: Event builder meta frame." << FairLogger::endl;
         if (!fIn->ReadBuffer(reinterpret_cast<char *>(df->hits), size - sizeof(DataFrame))) {
            return UnpackEventFrame(reinterpret_cast<Int_t *>(&buffer), size);
         }
      }
      LOG(DEBUG) << "ShipTdcSource: PartitionId " << std::hex << partitionId << std::dec << FairLogger::endl;
      if (!fIn->ReadBuffer(reinterpret_cast<char *>(df->hits), size - sizeof(DataFrame))) {

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
}

Bool_t ShipTdcSource::Unpack(Int_t *data, Int_t size, uint16_t partitionId)
{

   for (TObject *item : *fUnpackers) {
      auto unpacker = dynamic_cast<ShipUnpack *>(item);
      if (unpacker->GetPartition() == partitionId) {
         return unpacker->DoUnpack(data, size);
      }
   }

   LOG(WARNING) << "ShipTdcSource: Failed to find suitable unpacker." << FairLogger::endl;
   return kFALSE;
}

void ShipTdcSource::FillEventHeader(FairEventHeader *feh)
{
   feh->SetEventTime(fEventTime);
   feh->SetRunId(fRunId);
   return;
}

ClassImp(ShipTdcSource)
