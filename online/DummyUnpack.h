#ifndef ONLINE_DUMMYUNPACK_H
#define ONLINE_DUMMYUNPACK_H

#include "ShipUnpack.h"

class DummyUnpack : public ShipUnpack {
public:
   DummyUnpack(uint16_t PartitionId);

   /** Destructor. */
   virtual ~DummyUnpack();

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
   uint16_t fPartitionId;

   DummyUnpack(const DummyUnpack &);
   DummyUnpack &operator=(const DummyUnpack &);

public:
   // Class definition
   ClassDefOverride(DummyUnpack, 1)
};

#endif
