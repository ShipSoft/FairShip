// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

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

    /** Copy constructor **/
    SiliconTargetHit(const SiliconTargetHit& hit) = default;
    SiliconTargetHit& operator=(const SiliconTargetHit& hit) = default;

    /** Output to screen **/
    void Print();
    // void Print() const;
    Float_t GetSignal() const { return fSignal; };
    Double_t GetX() const { return fX; }
    Double_t GetY() const { return fY; }
    Double_t GetZ() const { return fZ; }

    constexpr int GetLayer() const { return floor(fDetectorID >> 17); }
    constexpr int GetPlane() const { return static_cast<int>(fDetectorID >> 16) % 2; }   // 0 is X-plane, 1 is Y-pane
    constexpr int GetColumn() const { return static_cast<int>(fDetectorID >> 14) % 4; }
    constexpr int GetRow() const { return static_cast<int>(fDetectorID >> 13) % 2; }
    constexpr int GetStrip() const { return static_cast<int>(fDetectorID % 4096); }
    constexpr int GetModule() const { return GetRow() + 1 + 2 * GetColumn(); }

    bool isValid() const { return flag; }

  private:
    Float_t fSignal;
    Double_t fX;
    Double_t fY;
    Double_t fZ;
    Float_t flag;

    ClassDef(SiliconTargetHit, 1);
};

#endif   // SND_SILICONTARGET_SILICONTARGETHIT_H_
