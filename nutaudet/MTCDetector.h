#ifndef MTCDETECTOR_H
#define MTCDETECTOR_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"
#include "TGeoMatrix.h"
#include "TClonesArray.h"
#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string
#include "MTCdetPoint.h"

#include "TVector3.h"
#include "TLorentzVector.h"

class MTCdetPoint;
class TGeoVolume;
class TGeoMedium;
class FairVolume;
class TClonesArray;

class MTCDetector : public FairDetector {
public:
    MTCDetector(const char* name, Double_t zCenter, Bool_t Active, const char* Title = "", Int_t DetId = 0);    MTCDetector();
    virtual ~MTCDetector();

    void SetMTCParameters(Double_t width, Double_t height,
                         Double_t ironThick, Double_t sciFiThick, Double_t scintThick,
                         Int_t nLayers, Double_t zCenter, Double_t fieldY);
    TGeoVolume* CreateSegmentedLayer(const char* name, Double_t width, Double_t height,
                            Double_t thickness, Double_t cellSizeX, Double_t cellSizeY,
                            TGeoMedium* material, Int_t color, Double_t transparency, Int_t LayerId);
    TGeoVolume* CreateSciFiModule(const char* name, Double_t width, Double_t height, Double_t thickness, Int_t LayerId);
    virtual void ConstructGeometry();
    virtual void Initialize();
    virtual Bool_t ProcessHits(FairVolume* vol = 0);
    MTCdetPoint* AddHit(Int_t trackID, Int_t detID,
        TVector3 pos, TVector3 mom,
        Double_t time, Double_t length,
        Double_t eLoss, Int_t pdgCode);

    virtual void Register();
    virtual void EndOfEvent();
    virtual TClonesArray* GetCollection(Int_t iColl) const;
    virtual void Reset();

private:

    /** Track information to be stored until the track leaves the
     active volume.
     */
     Int_t          fTrackID;           //!  track index
     Int_t          fPdgCode;           //!  pdg code
     Int_t          fVolumeID;          //!  volume id
     TLorentzVector fPos;               //!  position at entrance
     TLorentzVector fMom;               //!  momentum at entrance
     Double32_t     fTime;              //!  time
     Double32_t     fLength;            //!  length
     Double32_t     fELoss;             //!  energy loss
    Double_t fWidth;
    Double_t fHeight;
    Double_t fIronThick;
    Double_t fSciFiThick;
    Double_t fScintThick;
    Int_t fLayers;
    Double_t fZCenter;
    Double_t fFieldY;
    TClonesArray* fMTCDetectorPointCollection;

    MTCDetector(const MTCDetector&);
    MTCDetector& operator=(const MTCDetector&);
    Int_t InitMedium(const char* name);
    ClassDef(MTCDetector, 1)
};

#endif
