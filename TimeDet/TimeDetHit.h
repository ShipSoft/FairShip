// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef TIMEDET_TIMEDETHIT_H_
#define TIMEDET_TIMEDETHIT_H_
#include "FairVolume.h"
#include "ShipHit.h"
#include "TimeDetPoint.h"
#include "TObject.h"
#include "TGeoShape.h"
#include "TGeoPhysicalNode.h"


class TimeDetHit : public ShipHit
{
  public:

    /** Default constructor **/
    TimeDetHit();

    /** Constructor from TimeDetHit
     *@param detID    Detector ID
     *@param t_1, t_2      TDC on both sides
     *@param flag      True/False, in case of pile up
     **/
    TimeDetHit(TimeDetPoint* p, Double_t t0);

    /** Destructor **/
    virtual ~TimeDetHit();

    /** Copy constructor **/
    TimeDetHit(const TimeDetHit& point) = default;
    TimeDetHit& operator=(const TimeDetHit& point) = default;

    /** Accessors **/
    Double_t GetX() const;
    Double_t GetY() const;
    Double_t GetZ() const;
    TVector3 GetXYZ() const;
    TGeoNode* GetNode() const;
    std::vector<double> GetTime(Double_t x) const;
    std::vector<double> GetTime() const;
    std::vector<double> GetMeasurements() const;
    /** Modifier **/
    void SetTDC(Float_t val1, Float_t val2){t_1=val1;t_2=val2;}

    /** Output to screen **/
    virtual void Print() const;

    void Dist(Float_t x, Float_t& lpos, Float_t& lneg) const;
    Double_t Resol(Double_t x) const;
    void setInvalid() {flag = false;}
    void setIsValid() {flag = true;}
    bool isValid() const {return flag;}

  private:
    Double_t v_drift = 15.; // cm/ns
    Double_t par[4] = { 0.0272814, 109.303, 0, 0.0539487 };

    Float_t flag;     ///< flag
    Float_t t_1,t_2;  ///< TDC on both sides

    ClassDef(TimeDetHit, 2);

};

#endif  // TIMEDET_TIMEDETHIT_H_
