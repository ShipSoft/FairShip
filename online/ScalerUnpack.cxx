#include <cassert>

// ROOT headers
#include "TTree.h"
#include "ROOT/TSeq.hxx"

// Fair headers
#include "FairLogger.h"

// SHiP headers
#include "ScalerUnpack.h"
#include "ShipOnlineDataFormat.h"

// ScalerUnpack: Constructor
ScalerUnpack::ScalerUnpack(Short_t type, Short_t subType, Short_t procId, Short_t subCrate, Short_t control)
   : ShipUnpack(type, subType, procId, subCrate, control), fPartitionId(0x8100)
{
}

// Virtual ScalerUnpack: Public method
ScalerUnpack::~ScalerUnpack()
{
   LOG(INFO) << "ScalerUnpack: Delete instance" << FairLogger::endl;
}

// Init: Public method
Bool_t ScalerUnpack::Init()
{
   Register();
   return kTRUE;
}

// Register: Protected method
void ScalerUnpack::Register()
{
   LOG(INFO) << "ScalerUnpack : Registering..." << FairLogger::endl;
}

struct ScalerFrame {
   DataFrameHeader header;
   uint16_t PSW;
   uint16_t SPW;
   uint32_t PinStatus;
   uint32_t scalers[16];
   uint32_t slices[0];
   int getSliceCount() { return (header.size - 88) / sizeof(uint32_t); }
};

// DoUnpack: Public method
Bool_t ScalerUnpack::DoUnpack(Int_t *data, Int_t size)
{
   static_assert(sizeof(ScalerFrame) == 88);
   auto df = reinterpret_cast<ScalerFrame *>(data);
   LOG(INFO) << "ScalerUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;
   LOG(INFO) << "PSW = " << df->PSW << FairLogger::endl;
   LOG(INFO) << "SPW = " << df->SPW << FairLogger::endl;
   LOG(INFO) << "POT from SPS = " << df->scalers[0] << FairLogger::endl;
   LOG(INFO) << "S1raw = " << df->scalers[1] << FairLogger::endl;
   LOG(INFO) << "S1strobed = " << df->scalers[2] << FairLogger::endl;
   LOG(INFO) << "S1*S2 TrgRaw = " << df->scalers[3] << FairLogger::endl;
   LOG(INFO) << "S1*S2 TrgStrobed = " << df->scalers[4] << FairLogger::endl;
   for (auto i : ROOT::MakeSeq(df->getSliceCount())) {
      LOG(INFO) << "Slice " << i << "= " << df->slices[i] << FairLogger::endl;
   }
   std::vector<uint16_t> slices(df->slices, df->slices + df->getSliceCount());
   TTree *tree = new TTree("scalers", "scalers");
   tree->Branch("PSW", &(df->PSW));
   tree->Branch("SPW", &(df->SPW));
   tree->Branch("POTSPS", &(df->scalers[0]));
   tree->Branch("S1raw", &(df->scalers[1]));
   tree->Branch("S1strobed", &(df->scalers[2]));
   tree->Branch("TrgRaw", &(df->scalers[3]));
   tree->Branch("TrgStrobed", &(df->scalers[4]));
   tree->Branch("slices", "vector<uint16_t>", &slices);
   tree->Fill();
   tree->Write();
   return kTRUE;
}

// Reset: Public method
void ScalerUnpack::Reset()
{
   LOG(DEBUG) << "ScalerUnpack : Clearing Data Structure" << FairLogger::endl;
}

ClassImp(ScalerUnpack)
