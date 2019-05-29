#ifndef ONLINE_SCIFIUNPACK_H
#define ONLINE_SCIFIUNPACK_H

#include "ShipUnpack.h"

class SciFiUnpack : public ShipUnpack {
public:
   SciFiUnpack(uint16_t PartitionId);

   /** Destructor. */
   virtual ~SciFiUnpack();

   /** Initialization. Called once, before the event loop. */
   virtual Bool_t Init() override;

   /** Process an MBS sub-event. */
   virtual Bool_t DoUnpack(Int_t *data, Int_t size) override;

   /** Clear the output structures. */
   virtual void Reset() override;

   uint16_t GetPartition() override { return fPartitionId; }

protected:
   /** Register the output structures. */
   virtual void Register() override;

private:
   std::unique_ptr<TClonesArray> fRawData; /**< Array of output raw items. */
   Int_t fNHits = 0;                       /**< Number of raw items in current event. */
   Int_t fNHitsTotal = 0;                  /**< Total number of raw items. */
   uint16_t fPartitionId = 0x0900;

   SciFiUnpack(const SciFiUnpack &);
   SciFiUnpack &operator=(const SciFiUnpack &);

public:
   // Class definition
   ClassDefOverride(SciFiUnpack, 1)
};

#endif
