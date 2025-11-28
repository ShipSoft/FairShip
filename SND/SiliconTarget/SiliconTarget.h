// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef SND_SILICONTARGET_SILICONTARGET_H_
#define SND_SILICONTARGET_SILICONTARGET_H_

#include "FairDetector.h"
#include "ISTLPointContainer.h"
#include "Rtypes.h"
#include "SiliconTargetPoint.h"
#include "TClonesArray.h"
#include "TGeoMedium.h"
#include "TLorentzVector.h"
#include "TVector3.h"

#include <map>
#include <vector>

class SiliconTarget
    : public FairDetector
    , public ISTLPointContainer
{
  public:
    SiliconTarget(const char* name, Bool_t Active, const char* Title = "");
    SiliconTarget();
    virtual ~SiliconTarget();

    void SetSiliconTargetParameters(Double_t targetWidth,
                                    Double_t targetHeight,
                                    Double_t sensorWidth,
                                    Double_t sensorLength,
                                    Int_t nLayers,
                                    Double_t zPosition,
                                    Double_t targetThickness,
                                    Double_t targetSpacing,
                                    Double_t moduleOffset);

    TGeoVolume* CreateSiliconPlanes(const char* name,
                                    Double_t sensorWidth,
                                    Double_t sensorLength,
                                    Double_t planeSpacing,
                                    TGeoMedium* material,
                                    Int_t layerId);

    virtual void ConstructGeometry();
    /** Initialization of the detector is done here */
    virtual void Initialize();

    virtual Bool_t ProcessHits(FairVolume* vol = 0);

    SiliconTargetPoint* AddHit(Int_t trackID,
                               Int_t detID,
                               TVector3 pos,
                               TVector3 mom,
                               Double_t time,
                               Double_t length,
                               Double_t eLoss,
                               Int_t pdgCode);

    /** Registers the produced collections in FAIRRootManager */
    virtual void Register();
    virtual void EndOfEvent();
    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const;

    /** Update track indices in point collection (for std::vector migration) */
    void UpdatePointTrackIndices(const std::map<Int_t, Int_t>& indexMap);

    /** Has to be called after each event to reset the containers */
    virtual void Reset();

  private:
    /** Track information to be stored until the track leaves the
        active volume.
    */
    Int_t fTrackID;        //!  track index
    Int_t fPdgCode;        //!  pdg code
    Int_t fVolumeID;       //!  volume id
    TLorentzVector fPos;   //!  position at entrance
    TLorentzVector fMom;   //!  momentum at entrance
    Double32_t fTime;      //!  time
    Double32_t fLength;    //!  length
    Double32_t fELoss;     //!  energy loss
    Double_t fTargetWidth;
    Double_t fTargetHeight;
    Double_t fSensorWidth;
    Double_t fSensorLength;
    Int_t fLayers;
    Double_t fZPosition;
    Double_t fTargetThickness;
    Double_t fTargetSpacing;
    Double_t fModuleOffset;

    /** container for data points */
    std::vector<SiliconTargetPoint>* fSiliconTargetPoints;

    SiliconTarget(const SiliconTarget&);
    SiliconTarget& operator=(const SiliconTarget&);
    Int_t InitMedium(const char* name);
    ClassDef(SiliconTarget, 1)
};

#endif   // SND_SILICONTARGET_SILICONTARGET_H_
