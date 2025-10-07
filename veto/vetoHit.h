// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#ifndef VETO_VETOHIT_H_
#define VETO_VETOHIT_H_ 1
#include "ShipHit.h"

class vetoPoint;
class TGeoNode;

class vetoHit : public ShipHit
{
  public:
    /** Default constructor **/
    vetoHit();

    /** Constructor with arguments
     *@param detID    Detector ID
     *@param digi      digitized/measured ADC
     *@param flag      True/False, false if below threshold
     **/
    vetoHit(Int_t detID, Float_t adc);
    /** Destructor **/
    virtual ~vetoHit();

    /** Accessors **/
    Double_t GetX() const;
    Double_t GetY() const;
    Double_t GetZ() const;
    TVector3 GetXYZ() const;
    TGeoNode* GetNode() const;
    /** Modifier **/
    void SetEloss(Double_t val) { fdigi = val; }
    void SetTDC(Double_t val) { ft = val; }

    /** Output to screen **/

    virtual void Print(Int_t detID) const;
    Float_t GetADC() const { return fdigi; }
    Float_t GetTDC() const { return ft; }
    Double_t GetEloss() const { return fdigi; }
    void setInvalid() { flag = false; }
    void setIsValid() { flag = true; }
    bool isValid() const { return flag; }

    vetoHit(const vetoHit& point) = default;
    vetoHit& operator=(const vetoHit& point) = default;

  private:
    Double_t ft;
    Float_t flag;   ///< flag

    ClassDef(vetoHit, 1);
};

#endif   // VETO_VETOHIT_H_
