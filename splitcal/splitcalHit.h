#ifndef SPLITCAL_SPLITCALHIT_H_
#define SPLITCAL_SPLITCALHIT_H_


#include "ShipHit.h"
#include "splitcalPoint.h"
#include "TObject.h"
#include "TVector3.h"
#include <vector>

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
    splitcalHit(const std::vector<splitcalPoint>& points, Double_t t0);
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
    void SetIsUsed(int u) {_isUsed = u;}
    void SetXYZErrors(double xError, double yError, double zError) {_xError = xError; _yError = yError; _zError = zError;}

    double GetX() const { return _x; }
    double GetY() const { return _y; }
    double GetZ() const { return _z; }
    double GetEnergy() const { return _energy; }
    int GetIsPrecisionLayer() const { return _isPrecisionLayer; }
    int GetLayerNumber() const { return _nLayer; }
    int GetModuleXNumber() const { return _nModuleX; }
    int GetModuleYNumber() const { return _nModuleY; }
    int GetStripNumber() const { return _nStrip; }
    bool IsX() const { return _isX; }
    bool IsY() const { return _isY; }
    int IsUsed() const { return _isUsed; }
    double GetXError() const { return _xError; }
    double GetYError() const { return _yError; }
    double GetZError() const { return _zError; }

    /** Copy constructor **/
    splitcalHit(const splitcalHit& point) = default;
    splitcalHit& operator=(const splitcalHit& point) = default;

  private:

    Float_t flag;
    double _x, _y, _z, _xError, _yError, _zError;
    double _energy;
    int _isPrecisionLayer, _nLayer, _nModuleX, _nModuleY, _nStrip, _isUsed;
    bool _isX, _isY;

    ClassDef(splitcalHit,5);


};

#endif  // SPLITCAL_SPLITCALHIT_H_
