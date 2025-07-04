#ifndef PASSIVE_SHIPMUONSHIELD_H_
#define PASSIVE_SHIPMUONSHIELD_H_

#include "FairModule.h"                 // for FairModule
#include "FairLogger.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include "TGeoUniformMagField.h"
#include "TGeoMedium.h"
#include "TGeoShapeAssembly.h"
#include "TString.h"
#include <vector>
#include <array>
#include "TVectorT.h"

enum class FieldDirection : bool { up, down };

class ShipMuonShield : public FairModule
{
  public:
    ShipMuonShield(std::vector<double> in_params, Double_t z, const Bool_t WithConstShieldField, const Bool_t SC_key);
    ShipMuonShield();
    virtual ~ShipMuonShield();
    void ConstructGeometry();
    void SetSNDSpace(const Bool_t hole, Double_t hole_dx, Double_t hole_dy);
  protected:
    Double_t fMuonShieldHalfLength;   // FIXME: HA_field to be removed in the next workshop meeting
    Double_t dZ0, dZ1, dZ2, dZ3, dZ4, dZ5, dZ6, dZ7, dXgap, z_end_of_proximity_shielding;
    Int_t InitMedium(TString name);
    Bool_t fWithConstShieldField;
    Bool_t fSC_mag;
    std::vector<Double_t> shield_params;
    Bool_t snd_hole;
    Double_t snd_hole_dx = 0., snd_hole_dy = 0.;

    void CreateArb8(TString arbName,
                    TGeoMedium* medium,
                    Double_t dZ,
                    std::array<Double_t, 16> corners,
                    Int_t color,
                    TGeoUniformMagField* magField,
                    TGeoVolume* top,
                    Double_t x_translation,
                    Double_t y_translation,
                    Double_t z_translation,
                    const Bool_t snd_key = false);

    Int_t Initialize(std::vector<TString>& magnetName,
                     std::vector<FieldDirection>& fieldDirection,
                     std::vector<Double_t>& dXIn,
                     std::vector<Double_t>& dYIn,
                     std::vector<Double_t>& dXOut,
                     std::vector<Double_t>& dYOut,
                     std::vector<Double_t>& ratio_yokesIn,
                     std::vector<Double_t>& ratio_yokesOut,
                     std::vector<Double_t>& dY_yokeIn,
                     std::vector<Double_t>& dY_yokeOut,
                     std::vector<Double_t>& dZ,
                     std::vector<Double_t>& midGapIn,
                     std::vector<Double_t>& midGapOut,
                     std::vector<Double_t>& Bgoal,
                     std::vector<Double_t>& gapIn,
                     std::vector<Double_t>& gapOut,
                     std::vector<Double_t>& Z);

    void CreateMagnet(TString magnetName,
                      TGeoMedium* medium,
                      TGeoVolume* tShield,
                      TGeoUniformMagField* fields[4],
                      FieldDirection fieldDirection,
                      Double_t dX,
                      Double_t dY,
                      Double_t dX2,
                      Double_t dY2,
                      Double_t ratio_yoke_1,
                      Double_t ratio_yoke_2,
                      Double_t dY_yoke_1,
                      Double_t dY_yoke_2,
                      Double_t dZ,
                      Double_t middleGap,
                      Double_t middleGap2,
                      Double_t gap,
                      Double_t gap2,
                      Double_t Z,
                      Bool_t NotMagnet,
                      Bool_t SC_key);

  public:
    ClassDef(ShipMuonShield, 4)
};

#endif  // PASSIVE_SHIPMUONSHIELD_H_
