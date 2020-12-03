//  
//  Floor.h 
//   
//  by A. Buonaura
//
#ifndef Floor_H
#define Floor_H

#include "FairModule.h"                 // for FairModule
#include "Rtypes.h"                     // for Floor::Class, Bool_t, etc

#include <string>                       // for string

class Floor : public FairModule
{
  public:
    Floor(const char* name, const char* Title="Floor");
    Floor();
    virtual ~Floor();
    void ConstructGeometry();
    ClassDef(Floor,1)
    Int_t InitMedium(const char* name);

};

#endif //Floor_H

