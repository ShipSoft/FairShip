#ifndef TAUMAGNETICSPECTROMETER_H
#define TAUMAGNETICSPECTROMETER_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMagnet::Class, Bool_t, etc

#include <string>                       // for string

class ShipTAUMagneticSpectrometer : public FairModule
{
  public:
    ShipTAUMagneticSpectrometer(const char* name,const Double_t zLS,const Double_t FeL, const Double_t AirL, const Double_t SpectroL,
                                const Double_t GapV, const Double_t DGap, const Double_t MGap, const Double_t mf,
                                const char* Title="ShipTAUMagneticSpectrometer");
    ShipTAUMagneticSpectrometer();
    virtual ~ShipTAUMagneticSpectrometer();
    void ConstructGeometry();
    void Initialize();
    ClassDef(ShipTAUMagneticSpectrometer,1)
    
    
protected:
    Double_t zLastSlab; //z distance of the center of the last Fe slab of the second spectrometer in cm from the center of the vacuum tube
    Double_t IronLenght;
    Double_t AirLenght; // distance between the center of 2 iron slabs
    Double_t SpectrometerLenght;
    Double_t GapFromVacuum;
    Double_t DriftGap;
    Double_t MiddleGap;
    Double_t MagneticField;
};



#endif //TAUMAGNETICSPECTROMETER_H

