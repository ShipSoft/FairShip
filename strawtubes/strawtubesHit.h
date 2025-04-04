#ifndef STRAWTUBES_STRAWTUBESHIT_H_
#define STRAWTUBES_STRAWTUBESHIT_H_ 1

#include "ShipHit.h"
#include "TObject.h"
#include "TVector3.h"
#include "strawtubesPoint.h"

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
    void StrawEndPoints(TVector3& vbot, TVector3& vtop);
    /** Destructor **/
    virtual ~strawtubesHit();

    /** Output to screen **/
    virtual void Print() const;
    Float_t GetTDC() const { return fdigi; }
    void setInvalid() { flag = false; }
    bool isValid() const { return flag; }

    /** Copy constructor **/
    strawtubesHit(const strawtubesHit& point) = default;
    strawtubesHit& operator=(const strawtubesHit& point) = default;

  private:
    Float_t flag;   ///< flag

    ClassDef(strawtubesHit, 4);
};

#endif   // STRAWTUBES_STRAWTUBESHIT_H_
