// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef DETECTOR_DETECTOR_H_
#define DETECTOR_DETECTOR_H_

#include "FairDetector.h"
#include "ISTLPointContainer.h"
#include "TVector3.h"
#include "TLorentzVector.h"

#include "DetectorPoint.h"
#include <vector>

namespace SHiP{
class Detector: public FairDetector, public ISTLPointContainer {
    public:
        Detector() = default ;
        virtual ~Detector() = default;
        Detector(const char* Name, Bool_t Active);

        std::shared_ptr<DetectorPoint> AddHit(Int_t eventID, Int_t trackID, Int_t detID,
                              const TVector3& pos, const TVector3& mom, Double_t time,
                              Double_t length, Double_t eLoss, Int_t pdgCode,
                              const TVector3& Lpos, const TVector3& Lmom);

        /**  Create the detector geometry */
        virtual void ConstructGeometry();

    protected:

        /** Track information to be stored until the track leaves the active volume.*/
        Int_t fEventID;       //!  event index
        Int_t fTrackID;       //!  track index
        Int_t fVolumeID;      //!  volume id
        TLorentzVector fPos;  //!  position at entrance
        TLorentzVector fMom;  //!  momentum at entrance
        Double_t fTime;       //!  time
        Double_t fLength;     //!  length
        Double_t fELoss;      //!  energy loss
        std::vector<std::shared_ptr<DetectorPoint>> fDetPoints;

        TGeoVolume* fDetector = nullptr;  // Timing detector object
    private:
};
} // namespace SHiP

#endif // DETECTOR_DETECTOR_H_
