#ifndef PASSIVE_SHIPTARGETSTATION_H_
#define PASSIVE_SHIPTARGETSTATION_H_

#include "FairModule.h"                 // for FairModule
#include "Rtypes.h"                     // for ShipTargetStation::Class, Bool_t, etc
#include <string>                       // for string
#include <stdlib.h>

// C-AMM inside or outside class ? Maybe outside but in another header with other similar enum for other subdetectors ?
enum TargetVersion
{
    CDR = 18,    // tube geo
    Jun25 = 20   // tube geo
};

class ShipTargetStation : public FairModule
{
  public:
    ShipTargetStation(const char* name,
                      const Double_t tl,
                      const Double_t al,
                      const Double_t tz,
                      const Double_t az,
                      const TargetVersion tV,
                      const int nS,
                      const char* Title = "ShipTargetStation");
    ShipTargetStation(const char* name,
                      const Double_t tl,
                      const Double_t tz,
                      const TargetVersion tV,
                      const int nS,
                      const char* Title = "ShipTargetStation");
    ShipTargetStation();
    virtual ~ShipTargetStation();
    void ConstructGeometry();
    void SetLayerPosMat(Float_t d, std::vector<float> L, std::vector<float> G, std::vector<std::string> M)
    {
        fDiameter = d;
        // C-AMM better error reporting ?
        assert(fL.size() == fnS);
        fL = L;
        assert(fM.size() == fnS);
        fM = M;
        assert(fG.size() == fnS);
        fG = G;
    }
    ClassDef(ShipTargetStation, 5);

  protected:
    Double_t fTargetLength;        //
    Double_t fAbsorberLength;      //
    Double_t fAbsorberZ;           //
    Double_t fTargetZ;             //
    Double_t fDiameter;            //
    std::vector<float> fL;         // absorber width per layer
    std::vector<float> fG;         // gap after layer
    std::vector<std::string> fM;   // absorber material
    Int_t InitMedium(const char* name);
    Int_t fnS;
    TargetVersion fTV;
};
#endif // PASSIVE_SHIPTARGETSTATION_H_
