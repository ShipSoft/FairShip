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
#include "TClonesArray.h"

class TClonesArray;

class DriftTubeUnpack : public ShipUnpack {
public:
   DriftTubeUnpack();

   DriftTubeUnpack(bool charm);

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
   std::unique_ptr<TClonesArray> fRawTubes{new TClonesArray("MufluxSpectrometerHit")};
   std::unique_ptr<TClonesArray> fRawLateTubes{new TClonesArray("MufluxSpectrometerHit")};
   std::unique_ptr<TClonesArray> fRawScintillator{new TClonesArray("ScintillatorHit")};
   std::unique_ptr<TClonesArray> fRawBeamCounter{new TClonesArray("ScintillatorHit")};
   std::unique_ptr<TClonesArray> fRawMasterTrigger{new TClonesArray("ScintillatorHit")};
   std::unique_ptr<TClonesArray> fRawTriggers{new TClonesArray("ScintillatorHit")};
   uint16_t fPartitionId = 0x0C00;
   bool fCharm = false;

   DriftTubeUnpack(const DriftTubeUnpack &);
   DriftTubeUnpack &operator=(const DriftTubeUnpack &);

public:
   // Class definition
   ClassDefOverride(DriftTubeUnpack, 1)
};

#endif
