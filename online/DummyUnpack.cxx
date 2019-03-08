// SHiP headers
#include "DummyUnpack.h"
#include "ShipOnlineDataFormat.h"
#include "FairLogger.h"

// DummyUnpack: Constructor
DummyUnpack::DummyUnpack(uint16_t PartitionId) : fPartitionId(PartitionId) {}

// Virtual DummyUnpack: Public method
DummyUnpack::~DummyUnpack() = default;

// Init: Public method
Bool_t DummyUnpack::Init()
{
   Register();
   return kTRUE;
}

// Register: Protected method
void DummyUnpack::Register() {}

// DoUnpack: Public method
Bool_t DummyUnpack::DoUnpack(Int_t *data, Int_t size)
{
   LOG(INFO) << "DummyUnpack for PartitionId " << std::hex << fPartitionId << std::dec
             << ": Unpacking frame... size/bytes = " << size << FairLogger::endl;
   auto df = reinterpret_cast<DataFrame *>(data);
   switch (df->header.frameTime) {
   case SoS: LOG(INFO) << "DummyUnpack: SoS frame." << FairLogger::endl; return kTRUE;
   case EoS: LOG(INFO) << "DummyUnpack: EoS frame." << FairLogger::endl; return kTRUE;
   default: break;
   }

   return kTRUE;
}

// Reset: Public method
void DummyUnpack::Reset() {}

ClassImp(DummyUnpack)
