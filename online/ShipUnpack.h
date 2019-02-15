/********************************************************************************
 *    Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    *
 *                                                                              *
 *              This software is distributed under the terms of the             *
 *         GNU Lesser General Public Licence version 3 (LGPL) version 3,        *
 *                  copied verbatim in the file "LICENSE"                       *
 ********************************************************************************/

#ifndef ONLINE_SHIPUNPACK_H
#define ONLINE_SHIPUNPACK_H

#include "FairUnpack.h"
#include <memory>

class TClonesArray;

/**
 * An example unpacker of MBS data.
 */
class ShipUnpack : public FairUnpack {

public:
   ShipUnpack();

   /** Destructor. */
   virtual ~ShipUnpack();

   /** Initialization. Called once, before the event loop. */
   virtual Bool_t Init() override;

   /** Process an MBS sub-event. */
   virtual Bool_t DoUnpack(Int_t *data, Int_t size) override;

   /** Clear the output structures. */
   virtual void Reset() override;

   /** Method for controlling the functionality. */
   inline Int_t GetNHitsTotal() { return fNHitsTotal; }

   virtual uint16_t GetPartition() = 0;

protected:
   /** Register the output structures. */
   virtual void Register() override;

private:
   std::unique_ptr<TClonesArray> fRawData; /**< Array of output raw items. */
   Int_t fNHits;           /**< Number of raw items in current event. */
   Int_t fNHitsTotal;      /**< Total number of raw items. */
   uint16_t fPartitionId;

   ShipUnpack(const ShipUnpack &);
   ShipUnpack &operator=(const ShipUnpack &);

public:
   // Class definition
   ClassDefOverride(ShipUnpack, 1)
};

#endif
