//  
//  Floor.h 
//   
//  by A. Buonaura
// tunnel system from Fluka geometry added, T.Ruf Dec 2020
//
#ifndef Floor_H
#define Floor_H

#include "FairModule.h"                 // for FairModule
#include "Rtypes.h"                     // for Floor::Class, Bool_t, etc
#include "TGeoArb8.h"
#include "TVector3.h"

#include <string>                       // for string

class Floor : public FairModule
{
  public:
    Floor(const char* name, const char* Title="Floor");
    Floor();
    virtual ~Floor();
    void ConstructGeometry();
    void SetSND_Z(Double_t x){SND_Z = x;}
    TVector3 crossing(TVector3 H1,TVector3 H2,TVector3 H3,TVector3 P1,TVector3 P2,TVector3 P3);
    ClassDef(Floor,1)
    Int_t InitMedium(const char* name);

protected:
    
    Double_t SND_Z; // Position of SND with respect to FLUKA coordinate system origin at IP1

};

#endif //Floor_H

