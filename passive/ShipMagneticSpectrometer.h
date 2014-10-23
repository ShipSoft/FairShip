#ifndef MAGNETICSPECTROMETER_H
#define MAGNETICSPECTROMETER_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMagnet::Class, Bool_t, etc

#include <string>                       // for string

class ShipMagneticSpectrometer : public FairModule
{
  public:
    ShipMagneticSpectrometer(const char* name, const char* Title="OPERAlikeMagneticSpectrometer");
    ShipMagneticSpectrometer();
    virtual ~ShipMagneticSpectrometer();
    void ConstructGeometry();
    ClassDef(ShipMagneticSpectrometer,1)

};

#endif //MAGNETICSPECTROMETER_H

