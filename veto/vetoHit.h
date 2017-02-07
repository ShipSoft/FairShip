#ifndef vetoHIT_H
#define vetoHIT_H 1
#include "FairVolume.h"
#include "ShipHit.h"
#include "vetoPoint.h"
#include "TObject.h"
#include "TGeoShape.h"
#include "TGeoPhysicalNode.h"

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
    vetoHit(vetoPoint* p, Double_t t0);
    /** Destructor **/
    virtual ~vetoHit();

    /** Accessors **/   
    Int_t GetDetID(){return fVolumeId;}
    Double_t GetX(){return fVolumeX;}
    Double_t GetY(){return fVolumeY;}
    Double_t GetZ(){return fVolumeZ;}
    TVector3 GetXYZ(){return fVolumeXYZ;}

    
    /** Modifier **/
    void SetEloss(Double_t val){fEloss=val;}
    void SetDetID(Int_t val){fVolumeId=val;}
    void SetX(Double_t val){fVolumeX=val;}
    void SetY(Double_t val){fVolumeY=val;}
    void SetZ(Double_t val){fVolumeZ=val;}
    void SetXYZ(Double_t * val){fVolumeXYZ.SetX(val[0]);fVolumeXYZ.SetY(val[1]);fVolumeXYZ.SetZ(val[2]);}
    void SetXYZ(TVector3 val){fVolumeXYZ=val;}
     

    /** Output to screen **/

    virtual void Print(Int_t detID) const;
    Float_t adc() const {return fdigi;}
    Double_t GetEloss() {return fEloss;}
    void setInvalid() {flag = false;}
    void setIsValid() {flag = true;}
    bool isValid() const {return flag;}
  private:
    Double_t fEloss;
    Int_t    fVolumeId;
    Double_t fVolumeX;
    Double_t fVolumeY;
    Double_t fVolumeZ;
    TVector3 fVolumeXYZ;
    vetoHit(const vetoHit& point);
    vetoHit operator=(const vetoHit& point);

    Float_t flag;   ///< flag

    ClassDef(vetoHit,1);

};

#endif
