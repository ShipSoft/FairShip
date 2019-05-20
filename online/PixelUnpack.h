/********************************************************************************
 *    Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    *
 *                                                                              *
 *              This software is distributed under the terms of the             *
 *         GNU Lesser General Public Licence version 3 (LGPL) version 3,        *
 *                  copied verbatim in the file "LICENSE"                       *
 ********************************************************************************/

#ifndef ONLINE_PIXELUNPACK_H
#define ONLINE_PIXELUNPACK_H

#include "ShipUnpack.h"

class TClonesArray;

class PixelUnpack : public ShipUnpack {
public:
   PixelUnpack(uint16_t PartitionId);

   /** Destructor. */
   virtual ~PixelUnpack();

   /** Initialization. Called once, before the event loop. */
   virtual Bool_t Init() override;

   /** Process an MBS sub-event. */
   virtual Bool_t DoUnpack(Int_t *data, Int_t size) override;

   /** Clear the output structures. */
   virtual void Reset() override;

   /** Method for controlling the functionality. */
   inline Int_t GetNHitsTotal() { return fNHitsTotal; }

   uint16_t GetPartition() override { return fPartitionId; }

protected:
   /** Register the output structures. */
   virtual void Register() override;

private:
   TClonesArray *fRawData;        /**< Array of output raw items. */
   Int_t fNHits;              /**< Number of raw items in current event. */
   Int_t fNHitsTotal;         /**< Total number of raw items. */
   uint16_t fPartitionId;

   PixelUnpack(const PixelUnpack &);
   PixelUnpack &operator=(const PixelUnpack &);

public:
   // Class definition
   ClassDefOverride(PixelUnpack, 1)
};

#endif
