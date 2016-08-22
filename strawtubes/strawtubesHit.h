#ifndef STRAWTUBESHIT_H
#define STRAWTUBESHIT_H 1


#include "ShipHit.h"
#include "TObject.h"

class strawtubesHit : public ShipHit
{
  public:

    /** Default constructor **/
    strawtubesHit();

    /** Constructor with arguments
     *@param detID    Detector ID
     *@param tdc      digitized/measured TDC 
     **/
    strawtubesHit(Int_t detID, Float_t tdc);

    /** Destructor **/
    virtual ~strawtubesHit();

    /** Output to screen **/
    virtual void Print(Int_t detID) const;
    Float_t tdc() const {return ftdc;}

  private:
    /** Copy constructor **/
    strawtubesHit(const strawtubesHit& point);
    strawtubesHit operator=(const strawtubesHit& point);

    Float_t ftdc;
    ClassDef(strawtubesHit,1);
    

};

#endif
