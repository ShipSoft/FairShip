#ifndef vetoHIT_H
#define vetoHIT_H 1


#include "ShipHit.h"
#include "vetoPoint.h"
#include "TObject.h"

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
    vetoHit(Int_t detID, Float_t tdc);
    vetoHit(vetoPoint* p, Double_t t0);

    /** Destructor **/
    virtual ~vetoHit();

    /** Output to screen **/
    virtual void Print(Int_t detID) const;
    Float_t adc() const {return fdigi;}
    void setInvalid() {flag = false;}
    bool isValid() const {return flag;}

  private:
    /** Copy constructor **/
    vetoHit(const vetoHit& point);
    vetoHit operator=(const vetoHit& point);

    Float_t flag;   ///< flag

    ClassDef(vetoHit,1);
    

};

#endif
