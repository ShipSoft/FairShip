#include "ShipTdcSource.h"
#include "FairLogger.h"
#include "ShipOnlineDataFormat.h"

ShipTdcSource::ShipTdcSource() : FairOnlineSource() {}

ShipTdcSource::ShipTdcSource(const ShipTdcSource &source)
    : FairOnlineSource(source) {}

ShipTdcSource::~ShipTdcSource() {
}

Bool_t ShipTdcSource::Init(){
  fIn = new std::ifstream("tdcdata.bin", std::ios::binary);
  return true;
}

void ShipTdcSource::Close(){
  fIn->close();
}

Int_t ShipTdcSource::ReadEvent(UInt_t){
  auto df = new (buffer) DataFrame();
  if(fIn->read(reinterpret_cast<char *>(df),sizeof(DataFrame))){
    auto nhits = df->getHitCount();
    if(fIn->read(reinterpret_cast<char *>(df->hits), nhits * sizeof(RawDataHit))){
        if (Unpack(reinterpret_cast<Int_t*>(&buffer), sizeof(DataFrame) + nhits * sizeof(RawDataHit))){
          return 0;
        }
        LOG(WARNING) << "ShipTdcSource: Failed to Unpack." << FairLogger::endl;
        return 3;
    } 
    LOG(WARNING) << "ShipTdcSource: Failed to read hits." << FairLogger::endl;
    return 2;
  }
  return 1;
  LOG(WARNING) << "ShipTdcSource: Failed to read header." << FairLogger::endl;
}


Bool_t ShipTdcSource::Unpack(Int_t *data, Int_t size) {
  
  FairUnpack *unpack;
  unpack = static_cast<FairUnpack*>(fUnpackers->At(0));

  return unpack->DoUnpack(data, size);
}

ClassImp(ShipTdcSource)
