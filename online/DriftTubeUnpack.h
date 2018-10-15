/********************************************************************************
 *    Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    *
 *                                                                              *
 *              This software is distributed under the terms of the             *
 *         GNU Lesser General Public Licence version 3 (LGPL) version 3,        *
 *                  copied verbatim in the file "LICENSE"                       *
 ********************************************************************************/

#ifndef ONLINE_DRIFTTUBEUNPACK_H
#define ONLINE_DRIFTTUBEUNPACK_H

#include "ShipUnpack.h"
#include <memory>

class TClonesArray;

class DriftTubeUnpack : public ShipUnpack {
public:
   /** Standard Constructor. Input - MBS parameters of the detector. */
   DriftTubeUnpack(Short_t type = 94, Short_t subType = 9400, Short_t procId = 10, Short_t subCrate = 1,
                   Short_t control = 3);

   /** Destructor. */
   virtual ~DriftTubeUnpack();

   /** Initialization. Called once, before the event loop. */
   virtual Bool_t Init() override;

   /** Process an MBS sub-event. */
   virtual Bool_t DoUnpack(Int_t *data, Int_t size) override;

   /** Clear the output structures. */
   virtual void Reset() override;

   /** Method for controlling the functionality. */
   inline Int_t GetNHitsTotal() { return fNHitsTotalTubes + fNHitsTotalScintillator; }

   uint16_t GetPartition() override { return fPartitionId; }

protected:
   /** Register the output structures. */
   virtual void Register() override;

private:
   std::unique_ptr<TClonesArray> fRawTubes;        /**< Array of output raw items. */
   std::unique_ptr<TClonesArray> fRawScintillator; /**< Array of output raw items. */
   Int_t fNHitsTubes;              /**< Number of raw items in current event. */
   Int_t fNHitsScintillator;       /**< Number of raw items in current event. */
   Int_t fNHitsTotalTubes;         /**< Total number of raw items. */
   Int_t fNHitsTotalScintillator;  /**< Total number of raw items. */
   uint16_t fPartitionId;

   DriftTubeUnpack(const DriftTubeUnpack &);
   DriftTubeUnpack &operator=(const DriftTubeUnpack &);

public:
   // Class definition
   ClassDef(DriftTubeUnpack, 1)
};

#endif
