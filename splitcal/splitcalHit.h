#ifndef SPLITCALHIT_H
#define SPLITCALHIT_H 1


#include "ShipHit.h"
#include "splitcalPoint.h"
#include "TObject.h"
#include "TVector3.h"

class splitcalHit : public ShipHit
{
  public:

    /** Default constructor **/
    splitcalHit();

    /** Constructor with arguments
     *@param detID    Detector ID
     *@param digi      digitized/measured TDC 
     *@param flag      True/False, false if there is another hit with smaller tdc 
     **/
    splitcalHit(Int_t detID, Float_t tdc);
    splitcalHit(splitcalPoint* p, Double_t t0);
    /** Destructor **/
    virtual ~splitcalHit();

    /** Output to screen **/
    virtual void Print() const;
    Float_t GetTDC() const {return fdigi;}
    void setInvalid() {flag = false;}
    bool isValid() const {return flag;}

    std::string GetPaddedString(int& id); 
    std::string GetDetectorElementName(int& id);
    void Decoder(int& id, int& isPrecision, int& nLayer, int& nModuleX, int& nMdouleY, int& nStrip);
    void Decoder(std::string& encodedID, int& isPrecision, int& nLayer, int& nModuleX, int& nMdouleY, int& nStrip);

    void SetXYZ(double& x, double& y, double& z) {_x = x; _y = y; _z = z;}
    void SetIDs(int& isPrecision, int& nLayer, int& nModuleX, int& nModuleY, int& nStrip) {_isPrecisionLayer = isPrecision; _nLayer = nLayer; _nModuleX = nModuleX; _nModuleY=nModuleY; _nStrip = nStrip;} 
    void SetEnergy(double& e) {_energy = e;}
    void UpdateEnergy(double e) {_energy = _energy+e;}
    void SetIsX(bool x) {_isX = x;}
    void SetIsY(bool y) {_isY = y;}

    double GetX() {return _x;}
    double GetY() {return _y;}
    double GetZ() {return _z;}
    double GetEnergy() {return _energy;}
    int GetIsPrecisionLayer() {return _isPrecisionLayer;}
    int GetLayerNumber() {return _nLayer;}
    int GetModuleXNumber() {return _nModuleX;}
    int GetModuleYNumber() {return _nModuleY;}
    int GetStripNumber() {return _nStrip;}
    bool IsX() {return _isX;}
    bool IsY() {return _isY;}

  private:
    /** Copy constructor **/
    splitcalHit(const splitcalHit& point);
    splitcalHit operator=(const splitcalHit& point);

    Float_t flag;   
    double _x, _y, _z;
    double _energy;
    /* std::string _nameSubDetector;  */
    int _isPrecisionLayer, _nLayer, _nModuleX, _nModuleY, _nStrip;
    bool _isX, _isY;

    ClassDef(splitcalHit,3);
    

};

#endif
