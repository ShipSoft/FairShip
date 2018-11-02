#include <cassert>

// ROOT headers
#include "TTree.h"
#include "ROOT/TSeq.hxx"

// Fair headers
#include "FairLogger.h"
#include "FairRootManager.h"
#include "FairRootFileSink.h"

// SHiP headers
#include "ScalerUnpack.h"
#include "ShipOnlineDataFormat.h"

// ScalerUnpack: Constructor
ScalerUnpack::ScalerUnpack() : fPartitionId(0x8100) {}

// Virtual ScalerUnpack: Public method
ScalerUnpack::~ScalerUnpack() = default;

// Init: Public method
Bool_t ScalerUnpack::Init()
{
   Register();
   fMan = FairRootManager::Instance();
   return kTRUE;
}

// Register: Protected method
void ScalerUnpack::Register()
{
   LOG(DEBUG) << "ScalerUnpack : Registering..." << FairLogger::endl;
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
   static_assert(sizeof(ScalerFrame) == 88, "Scaler frame size incorrect!");
   auto df = reinterpret_cast<ScalerFrame *>(data);
   LOG(DEBUG) << "ScalerUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;
   LOG(DEBUG) << "PSW = " << df->PSW << FairLogger::endl;
   LOG(DEBUG) << "SPW = " << df->SPW << FairLogger::endl;
   LOG(DEBUG) << "POT from SPS = " << df->scalers[0] << FairLogger::endl;
   LOG(DEBUG) << "S1raw = " << df->scalers[1] << FairLogger::endl;
   LOG(DEBUG) << "S1strobed = " << df->scalers[2] << FairLogger::endl;
   LOG(DEBUG) << "S1*S2 TrgRaw = " << df->scalers[3] << FairLogger::endl;
   LOG(DEBUG) << "S1*S2 TrgStrobed = " << df->scalers[4] << FairLogger::endl;
   for (auto i : ROOT::MakeSeq(df->getSliceCount())) {
      LOG(DEBUG) << "Slice " << i << "= " << df->slices[i] << FairLogger::endl;
   }
   auto sink = fMan->GetSink();
   assert(sink->GetSinkType() == kFILESINK);
   auto rootFileSink = dynamic_cast<FairRootFileSink*>(sink);
   auto f = rootFileSink->GetRootFile();
   tree = dynamic_cast<TTree *>(f->Get("scalers"));
   if (tree == nullptr) {
      tree = new TTree("scalers", "scalers");
   }
   tree->Branch("PSW", &(df->PSW));
   tree->Branch("SPW", &(df->SPW));
   for (auto i : ROOT::MakeSeq(16)) {
      tree->Branch(TString::Format("SC%.2d", i), &(df->scalers[i]));
   }
   std::vector<uint32_t> slices(df->slices, df->slices + df->getSliceCount());
   tree->Branch("slices", "vector<uint32_t>", &slices);
   tree->Fill();
   tree->Write("", TObject::kOverwrite);
   return kTRUE;
}

// Reset: Public method
void ScalerUnpack::Reset()
{
   LOG(DEBUG) << "ScalerUnpack : Clearing Data Structure" << FairLogger::endl;
}

ClassImp(ScalerUnpack)
