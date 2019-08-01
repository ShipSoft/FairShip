#ifndef ONLINE_SHIPTDCSOURCE_H
#define ONLINE_SHIPTDCSOURCE_H

#include <map>
#include "FairOnlineSource.h"
#include "TObjArray.h"
#include "TFile.h"

#include "FairUnpack.h"

class FairEventHeader;

class ShipTdcSource : public FairOnlineSource {
public:
   ShipTdcSource();
   explicit ShipTdcSource(TString filename);
   ShipTdcSource(const ShipTdcSource &source);
   virtual ~ShipTdcSource();

   virtual Bool_t Init();
   virtual Int_t ReadEvent(UInt_t = 0); // Read frame by frame
   virtual void Close();
   void FillEventHeader(FairEventHeader *feh);
   inline void AddUnpacker(uint16_t partitionId, FairUnpack *unpacker)
   {
      fUnpackerMap[partitionId] = unpacker;
      fUnpackers->Add(unpacker);
   }

protected:
   Bool_t Unpack(Int_t *data, Int_t size, uint16_t partitionId);
   Int_t UnpackEventFrame(Int_t *data, Int_t total_size);
   TFile *fIn;
   unsigned char buffer[UINT16_MAX];
   Double_t fEventTime = 0;
   std::map<uint16_t, FairUnpack *> fUnpackerMap{};

   TString fFilename;

   ClassDef(ShipTdcSource, 1)
};

#endif
