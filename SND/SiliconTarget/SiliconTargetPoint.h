// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef SND_SILICONTARGET_SILICONTARGETPOINT_H_
#define SND_SILICONTARGET_SILICONTARGETPOINT_H_ 1

#include "FairMCPoint.h"
#include "TObject.h"
#include "TVector3.h"

class SiliconTargetPoint : public FairMCPoint
{

  public:
    /** Default constructor **/
    SiliconTargetPoint();

    /** Constructor with arguments
     *@param trackID  Index of MCTrack
     *@param detID    Detector ID
     *@param pos      Ccoordinates at entrance to active volume [cm]
     *@param mom      Momentum of track at entrance [GeV]
     *@param tof      Time since event start [ns]
     *@param length   Track length since creation [cm]
     *@param eLoss    Energy deposit [GeV]
     *@param pdgcode  PDG code of MCTrack
     **/

    SiliconTargetPoint(Int_t trackID,
                       Int_t detID,
                       TVector3 pos,
                       TVector3 mom,
                       Double_t tof,
                       Double_t length,
                       Double_t eLoss,
                       Int_t pdgcode);

    /** Destructor **/
    virtual ~SiliconTargetPoint();

    /** Copy constructor **/
    SiliconTargetPoint(const SiliconTargetPoint& point) = default;
    SiliconTargetPoint& operator=(const SiliconTargetPoint& point) = default;

    /** Output to screen **/
    virtual void Print() const;
    Int_t PdgCode() const { return fPdgCode; }

    constexpr int GetLayer() const { return floor(fDetectorID >> 17); }
    constexpr int GetPlane() const { return static_cast<int>(fDetectorID >> 16) % 2; }   // 0 is X-plane, 1 is Y-pane
    constexpr int GetColumn() const { return static_cast<int>(fDetectorID >> 14) % 4; }
    constexpr int GetRow() const { return static_cast<int>(fDetectorID >> 13) % 2; }
    constexpr int GetStrip() const { return static_cast<int>(fDetectorID % 4096); }
    constexpr int GetModule() const { return GetRow() + 1 + 2 * GetColumn(); }

  private:
    Int_t fPdgCode;

    ClassDef(SiliconTargetPoint, 2)
};

#endif   // SND_SILICONTARGET_SILICONTARGETPOINT_H_
