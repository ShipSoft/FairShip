/********************************************************************************
 *    Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    *
 *                                                                              *
 *              This software is distributed under the terms of the             *
 *         GNU Lesser General Public Licence version 3 (LGPL) version 3,        *
 *                  copied verbatim in the file "LICENSE"                       *
 ********************************************************************************/

#ifndef ONLINE_SCALERUNPACK_H
#define ONLINE_SCALERUNPACK_H

#include "ShipUnpack.h"

class FairRootManager;
class TTree;

class ScalerUnpack : public ShipUnpack {
public:
   /** Standard Constructor. Input - MBS parameters of the detector. */
   ScalerUnpack(Short_t type = 94, Short_t subType = 9400, Short_t procId = 10, Short_t subCrate = 1,
                Short_t control = 3);

   /** Destructor. */
   virtual ~ScalerUnpack();

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
   FairRootManager *fMan;
   TTree *tree;

   ScalerUnpack(const ScalerUnpack &);
   ScalerUnpack &operator=(const ScalerUnpack &);

public:
   // Class definition
   ClassDef(ScalerUnpack, 1)
};

#endif
