#include <cassert>

// ROOT headers
#include "TTree.h"
#include "ROOT/TSeq.hxx"

// Fair headers
#include "FairLogger.h"
#include "FairRootManager.h"

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

struct ScalarFrame {
   DataFrameHeader header;
   uint16_t PSW;
   uint16_t SPW;
   uint32_t PinStatus;
   uint32_t scalars[16];
   uint32_t slices[0];
   int getSliceCount() { return (header.size - 88) / sizeof(uint32_t); }
};

// DoUnpack: Public method
Bool_t ScalerUnpack::DoUnpack(Int_t *data, Int_t size)
{
   static_assert(sizeof(ScalarFrame) == 88, "Scaler frame size incorrect!");
   auto df = reinterpret_cast<ScalarFrame *>(data);
   LOG(DEBUG) << "ScalerUnpack : Unpacking frame... size/bytes = " << size << FairLogger::endl;
   LOG(DEBUG) << "PSW = " << df->PSW << FairLogger::endl;
   LOG(DEBUG) << "SPW = " << df->SPW << FairLogger::endl;
   LOG(DEBUG) << "POT from SPS = " << df->scalars[0] << FairLogger::endl;
   LOG(DEBUG) << "S1raw = " << df->scalars[1] << FairLogger::endl;
   LOG(DEBUG) << "S1strobed = " << df->scalars[2] << FairLogger::endl;
   LOG(DEBUG) << "S1*S2 TrgRaw = " << df->scalars[3] << FairLogger::endl;
   LOG(DEBUG) << "S1*S2 TrgStrobed = " << df->scalars[4] << FairLogger::endl;
   for (auto i : ROOT::MakeSeq(df->getSliceCount())) {
      LOG(DEBUG) << "Slice " << i << "= " << df->slices[i] << FairLogger::endl;
   }
   auto f = fMan->GetOutFile();
   tree = dynamic_cast<TTree *>(f->Get("scalers"));
   if (tree == nullptr) {
      tree = new TTree("scalers", "scalers");
   }
   tree->Branch("PSW", &(df->PSW));
   tree->Branch("SPW", &(df->SPW));
   for (auto i : ROOT::MakeSeq(16)) {
      switch (i) {
      case 11: {
         int goliath = int(df->scalars[i]) / 0x10000;
         int david = int(df->scalars[i]) % 0x10000;
         tree->Branch("Goliath", &goliath);
         tree->Branch("David", &david);
         break;
      }
      case 12: tree->Branch("spill_type", &(df->scalars[i])); break;
      default: tree->Branch(TString::Format("SC%.2d", i), &(df->scalars[i]));
      }
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
