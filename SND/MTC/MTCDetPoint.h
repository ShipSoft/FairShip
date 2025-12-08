// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef SND_MTC_MTCDETPOINT_H_
#define SND_MTC_MTCDETPOINT_H_ 1

#include "FairMCPoint.h"
#include "TObject.h"
#include "TVector3.h"

class MTCDetPoint : public FairMCPoint
{

  public:
    /** Default constructor **/
    MTCDetPoint();

    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/

    MTCDetPoint(Int_t trackID,
                Int_t detID,
                TVector3 pos,
                TVector3 mom,
                Double_t tof,
                Double_t length,
                Double_t eLoss,
                Int_t pdgcode);

    /** Destructor **/
    virtual ~MTCDetPoint();

    /** Copy constructor **/
    MTCDetPoint(const MTCDetPoint& point) = default;
    MTCDetPoint& operator=(const MTCDetPoint& point) = default;

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const { return fPdgCode; }
    Int_t GetLayer() const
    {
        return static_cast<int>(fDetectorID / 1000000) % 100;
    }
    Int_t GetLayerType() const
    {
        return static_cast<int>(fDetectorID / 100000) % 10;
    }
    Int_t fPdgCode;

    ClassDef(MTCDetPoint, 3)
};

#endif   // SND_MTC_MTCDETPOINT_H_
