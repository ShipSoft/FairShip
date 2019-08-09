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

class TClonesArray;

class DriftTubeUnpack : public ShipUnpack {
public:
   DriftTubeUnpack();

   /** Destructor. */
   virtual ~DriftTubeUnpack();

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
   std::unique_ptr<TClonesArray> fRawTubes;        /**< Array of output raw items. */
   std::unique_ptr<TClonesArray> fRawLateTubes;        /**< Array of output raw items. */
   std::unique_ptr<TClonesArray> fRawScintillator; /**< Array of output raw items. */
   std::unique_ptr<TClonesArray> fRawBeamCounter; /**< Array of output raw items. */
   std::unique_ptr<TClonesArray> fRawMasterTrigger; /**< Array of output raw items. */
   std::unique_ptr<TClonesArray> fRawTriggers; /**< Array of output raw items. */
   uint16_t fPartitionId;

   DriftTubeUnpack(const DriftTubeUnpack &);
   DriftTubeUnpack &operator=(const DriftTubeUnpack &);

public:
   // Class definition
   ClassDefOverride(DriftTubeUnpack, 1)
};

#endif
