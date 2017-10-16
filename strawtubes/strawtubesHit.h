#ifndef STRAWTUBESHIT_H
#define STRAWTUBESHIT_H 1


#include "ShipHit.h"
#include "strawtubesPoint.h"
#include "TObject.h"
#include "TVector3.h"

class strawtubesHit : public ShipHit
{
  public:

    /** Default constructor **/
    strawtubesHit();

    /** Constructor with arguments
     *@param detID    Detector ID
     *@param digi      digitized/measured TDC 
     *@param flag      True/False, false if there is another hit with smaller tdc 
     **/
    strawtubesHit(Int_t detID, Float_t tdc);
    strawtubesHit(strawtubesPoint* p, Double_t t0);
    void StrawEndPoints(TVector3 &vbot, TVector3 &vtop);  
/** Destructor **/
    virtual ~strawtubesHit();

    /** Output to screen **/
    virtual void Print() const;
    Float_t GetTDC() const {return fdigi;}
    void setInvalid() {flag = false;}
    bool isValid() const {return flag;}

  private:
    /** Copy constructor **/
    strawtubesHit(const strawtubesHit& point);
    strawtubesHit operator=(const strawtubesHit& point);

    Float_t flag;   ///< flag

    ClassDef(strawtubesHit,3);
    

};

#endif
