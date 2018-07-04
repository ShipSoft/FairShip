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
/* #include <type_traits> */
/* #include <typeinfo> */

class TClonesArray;

/**
 * An example unpacker of MBS data.
 */
/* template <class HitType> */
class ShipUnpack : public FairUnpack {
   /* static_assert(std::is_base_of<ShipHit, HitType>::value); */

public:
   /** Standard Constructor. Input - MBS parameters of the detector. */
   ShipUnpack(Short_t type = 94, Short_t subType = 9400, Short_t procId = 10, Short_t subCrate = 1,
              Short_t control = 3);

   /** Destructor. */
   virtual ~ShipUnpack();

   /** Initialization. Called once, before the event loop. */
   virtual Bool_t Init();

   /** Process an MBS sub-event. */
   virtual Bool_t DoUnpack(Int_t *data, Int_t size);

   /** Clear the output structures. */
   virtual void Reset();

   /** Method for controling the functionality. */
   inline Int_t GetNHitsTotal() { return fNHitsTotal; }

   virtual uint16_t GetPartition()=0;

protected:
   /** Register the output structures. */
   virtual void Register();

private:
   TClonesArray *fRawData; /**< Array of output raw items. */
   Int_t fNHits;           /**< Number of raw items in current event. */
   Int_t fNHitsTotal;      /**< Total number of raw items. */
   uint16_t fPartitionId;

   ShipUnpack(const ShipUnpack &);
   ShipUnpack &operator=(const ShipUnpack &);

public:
   // Class definition
   ClassDef(ShipUnpack, 1)
};

/* template <> */
/* Bool_t ShipUnpack<MufluxSpectrometerHit>::DoUnpack(Int_t *data, Int_t size); */

#endif
