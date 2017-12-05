#ifndef MUONHIT_H
#define MUONHIT_H 1

#include "ShipHit.h"
#include "muonPoint.h"
#include "TObject.h"
#include "TVector3.h"

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
    muonHit(Int_t detID, Float_t tdc);
    muonHit(muonPoint* p, Double_t t0);

    Int_t fromXYZ(TVector3 p);    // should provide the mapping, true xyz to detectorID
    void XYZfromDetID(TVector3 &p);  // should return centre of muon tile  
/** Destructor **/
    virtual ~muonHit();

    /** Output to screen **/
    virtual void Print() const;
    Float_t GetTDC() const {return fdigi;}
    void setInvalid() {flag = false;}
    bool isValid() const {return flag;}

  private:
    /** Copy constructor **/
    muonHit(const muonHit& point);
    muonHit operator=(const muonHit& point);

    Float_t flag;   ///< flag

    ClassDef(muonHit,1);
    
};

#endif
