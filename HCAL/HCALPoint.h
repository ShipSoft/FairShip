// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef HCAL_HCALPOINT_H_
#define HCAL_HCALPOINT_H_


#include "FairMCPoint.h"

#include "TObject.h"
#include "TVector3.h"

class HCALPoint : public FairMCPoint
{

  public:

    /** Default constructor **/
    HCALPoint();


    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     **/
    HCALPoint(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                     Double_t tof, Double_t length, Double_t eLoss, Int_t pdgCode);



    /** Destructor **/
    virtual ~HCALPoint();

    /** Copy constructor **/
    HCALPoint(const HCALPoint& point) = default;
    HCALPoint& operator=(const HCALPoint& point) = default;

    /** Output to screen **/
    /* virtual void Print(const Option_t* opt) const; */
    virtual void Print() const;
    Int_t PdgCode() const {return fPdgCode;}

  private:
    Int_t fPdgCode;

    ClassDef(HCALPoint, 3)
};

#endif  
