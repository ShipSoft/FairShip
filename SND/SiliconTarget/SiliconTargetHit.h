#ifndef SND_SILICONTARGET_SILICONTARGETHIT_H_
#define SND_SILICONTARGET_SILICONTARGETHIT_H_ 1

#include "ShipHit.h"
#include "SiliconTargetPoint.h"
#include "TObject.h"
#include "TVector3.h"

class SiliconTargetHit : public ShipHit
{
  public:
    /** Default constructor **/
    SiliconTargetHit();
    // SiliconTargetHit(Int_t detID);

    //  Constructor from SiliconTargetPoint
    SiliconTargetHit(Int_t detID, const std::vector<SiliconTargetPoint*>&);

    /** Destructor **/
    virtual ~SiliconTargetHit();

    /** Output to screen **/
    void Print();
    // void Print() const;
    Float_t GetSignal() { return fSignal; };
    Double_t GetX() { return fX; }
    Double_t GetY() { return fY; }
    Double_t GetZ() { return fZ; }

    int constexpr GetLayer() { return floor(fDetectorID >> 17); }
    int constexpr GetPlane() { return static_cast<int>(fDetectorID >> 16) % 2; }   // 0 is X-plane, 1 is Y-pane
    int constexpr GetColumn() { return static_cast<int>(fDetectorID >> 14) % 4; }
    int constexpr GetRow() { return static_cast<int>(fDetectorID >> 13) % 2; }
    int constexpr GetStrip() { return static_cast<int>(fDetectorID % 4096); }
    int constexpr GetModule() { return GetRow() + 1 + 2 * GetColumn(); }

    bool isValid() const { return flag; }

  private:
    /** Copy constructor **/
    SiliconTargetHit(const SiliconTargetHit& hit) = default;
    SiliconTargetHit& operator=(const SiliconTargetHit& hit) = default;

    Float_t fSignal;
    Double_t fX;
    Double_t fY;
    Double_t fZ;
    Float_t flag;

    ClassDef(SiliconTargetHit, 1);
};

#endif   // SND_SILICONTARGET_SILICONTARGETHIT_H_
