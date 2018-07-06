#ifndef ONLINE_SHIPTDCSOURCE_H
#define ONLINE_SHIPTDCSOURCE_H

#include "FairOnlineSource.h"
#include "TObjArray.h"

#include "FairUnpack.h"

class ShipTdcSource : public FairOnlineSource {
public:
   ShipTdcSource();
   ShipTdcSource(std::string filename);
   ShipTdcSource(const ShipTdcSource &source);
   virtual ~ShipTdcSource();

   virtual Bool_t Init();
   virtual Int_t ReadEvent(UInt_t = 0); // Read frame by frame
   virtual void Close();

protected:
   Bool_t Unpack(Int_t *data, Int_t size, uint16_t partitionId);
   std::ifstream *fIn;
   unsigned char buffer[UINT16_MAX];
   std::string fFilename;

   ClassDef(ShipTdcSource, 0)
};

#endif
