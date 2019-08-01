#include <stdexcept>
#include "ShipTdcSource.h"
#include "FairLogger.h"
#include "FairEventHeader.h"
#include "ShipUnpack.h"
#include "ShipOnlineDataFormat.h"

ShipTdcSource::ShipTdcSource() : fFilename("tdcdata.bin") {}

ShipTdcSource::ShipTdcSource(TString filename) : fFilename(std::move(filename)) {}

ShipTdcSource::ShipTdcSource(const ShipTdcSource &source) : FairOnlineSource(source) {}

ShipTdcSource::~ShipTdcSource() = default;

Bool_t ShipTdcSource::Init()
{
   fIn = TFile::Open(fFilename + "?filetype=raw", "read");
   return kTRUE;
}

void ShipTdcSource::Close()
{
   LOG(DEBUG) << "Closing file " << fFilename << FairLogger::endl;
   fIn->Close();
}

Int_t ShipTdcSource::UnpackEventFrame(Int_t *data, Int_t total_size)
{
   auto mf = reinterpret_cast<DataFrame *>(data);
   total_size -= sizeof(DataFrame);
   data = reinterpret_cast<Int_t *>(&(mf->hits));
   auto frameTime = mf->header.frameTime;
   switch (frameTime) {
   case SoS: LOG(INFO) << "ShipTdcSource: SoS frame." << FairLogger::endl; return 2;
   case EoS: LOG(INFO) << "ShipTdcSource: EoS frame." << FairLogger::endl; break;
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
   return (frameTime == EoS) ? 1 : 0;
}

Int_t ShipTdcSource::ReadEvent(UInt_t)
{
   auto df = new (buffer) DataFrame();
   if (!fIn->ReadBuffer(reinterpret_cast<char *>(df), sizeof(DataFrame))) {
      size_t size = df->header.size;
      auto frameTime = df->header.frameTime;
      switch (frameTime) {
      case SoS: LOG(INFO) << "ShipTdcSource: SoS frame." << FairLogger::endl; break;
      case EoS: LOG(INFO) << "ShipTdcSource: EoS frame." << FairLogger::endl; break;
      default: break;
      }
      fEventTime = double(frameTime) * 25;
      uint16_t partitionId = df->header.partitionId;
      if (partitionId == 0x8000) {
         LOG(DEBUG) << "ShipTdcSource: Event builder meta frame." << FairLogger::endl;
         assert(size - sizeof(DataFrame) > 0);
         if (!fIn->ReadBuffer(reinterpret_cast<char *>(df->hits), size - sizeof(DataFrame))) {
            if (fEventTime > 5000000000 && frameTime != EoS && frameTime != SoS) {
               LOG(WARNING) << "Late event:" << FairLogger::endl;
               for (int i = 0; i < size; i++) {
                  if (i % 4 == 0) {
                     std::cout << ' ';
                  } else if (i % 16 == 0) {
                     std::cout << '\n';
                  }
                  std::cout << std::hex << +buffer[i] << std::dec;
               }
               std::cout << std::endl;
            }
            return UnpackEventFrame(reinterpret_cast<Int_t *>(&buffer), size);
         }
      }
      LOG(DEBUG) << "ShipTdcSource: PartitionId " << std::hex << partitionId << std::dec << FairLogger::endl;
      if (!fIn->ReadBuffer(reinterpret_cast<char *>(df->hits), size - sizeof(DataFrame))) {

         if (Unpack(reinterpret_cast<Int_t *>(&buffer), size, partitionId)) {
            return (frameTime == EoS) ? 1 : 0;
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
   try {
      return fUnpackerMap.at(partitionId)->DoUnpack(data, size);
   } catch (const std::out_of_range &oor) {
      LOG(WARNING) << "ShipTdcSource: Failed to find suitable unpacker." << FairLogger::endl;
      return kFALSE;
   }
}

void ShipTdcSource::FillEventHeader(FairEventHeader *feh)
{
   // TODO add frame times per partition?, -1 if not present?
   feh->SetEventTime(fEventTime);
   feh->SetRunId(fRunId);
   return;
}

ClassImp(ShipTdcSource)
