#ifndef MUONHIT_H
#define MUONHIT_H 1

#include "TObject.h"
#include "TVector3.h"

#include "ShipHit.h"
#include "muonPoint.h"


class muonHit : public ShipHit
{
  public:

    /** Default constructor **/
    muonHit();

    /** Constructor with arguments
     *@param detID    Detector ID
     *@param digi      digitized/measured TDC 
     *@param flag      True/False, false if there is another hit with smaller tdc 
     **/
    muonHit(Int_t detID, Float_t digi, Bool_t isValid);
    muonHit(muonPoint* p, Double_t t0);

    Int_t DetIDfromXYZ(TVector3 p); //provide mapping, true xyz to detectorID
    TVector3 XYZfromDetID(Int_t detID);  // return centre of muon tile  
/** Destructor **/
    virtual ~muonHit();

    /** Output to screen **/
    virtual void Print() const;
//
    TVector3 getPos() {return XYZfromDetID(fDetectorID);}
    Bool_t isValid() const {return hisV;}
//
    Double_t SetMuonTimeRes(Double_t mcTime); // return tdc
    void setValidity(Bool_t isValid);
//
  private:
    /** Copy constructor **/
    muonHit(const muonHit& point);
    muonHit operator=(const muonHit& point);

    Float_t flag;   ///< flag

    static bool onlyOnce;
    void stInit(); // stations init
//
    Bool_t hisV;
//
    ClassDef(muonHit,3)
};

#endif  //MUONHIT.H
