#ifndef MTCDETECTOR_H_
#define MTCDETECTOR_H_

#include "FairDetector.h"
#include "FairModule.h"   // for FairModule
#include "MtcDetPoint.h"
#include "Rtypes.h"   // for ShipMuonShield::Class, Bool_t, etc
#include "TClonesArray.h"
#include "TGeoMatrix.h"
#include "TLorentzVector.h"
#include "TVector3.h"

#include <string>   // for string

class MtcDetPoint;
class TGeoVolume;
class TGeoVolumeAssembly;
class TGeoMedium;
class FairVolume;
class TClonesArray;

class MTCDetector : public FairDetector
{
  public:
    MTCDetector(const char* name, Bool_t Active, const char* Title = "", Int_t DetId = 0);
    MTCDetector();
    virtual ~MTCDetector();

    void SetMTCParameters(Double_t width,
                          Double_t height,
                          Double_t angle,
                          Double_t ironThick,
                          Double_t sciFiThick,
                          Double_t scintThick,
                          Int_t nLayers,
                          Double_t zCenter,
                          Double_t fieldY);
    virtual void CreateScintModule(const char* name,
                                   TGeoVolumeAssembly* modMotherVol,
                                   Double_t z_shift,
                                   Double_t width,
                                   Double_t height,
                                   Double_t thickness,
                                   Double_t cellSizeX,
                                   Double_t cellSizeY,
                                   TGeoMedium* material,
                                   Int_t color,
                                   Double_t transparency,
                                   Int_t LayerId);
    virtual void CreateSciFiModule(const char* name,
                                   TGeoVolumeAssembly* modMotherVol,
                                   Double_t width,
                                   Double_t height,
                                   Double_t thickness,
                                   Int_t LayerId);
    virtual void ConstructGeometry();
    virtual void Initialize();
    /** Get position of single fibre in global coordinate system**/
    void GetPosition(Int_t fDetectorID, TVector3& vLeft, TVector3& vRight);   // or top and bottom
    /** Transform global position to local position in plane **/
    TVector3 GetLocalPos(Int_t fDetectorID, TVector3* glob);
    /** mean position of fibre2 associated with SiPM channel **/
    void GetSiPMPosition(Int_t SiPMChan, TVector3& A, TVector3& B);
    Double_t ycross(Double_t a, Double_t R, Double_t x);
    Double_t integralSqrt(Double_t ynorm);
    Double_t fraction(Double_t R, Double_t x, Double_t y);
    Double_t area(Double_t a, Double_t R, Double_t xL, Double_t xR);
    void SiPMmapping();
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetSiPMmapU() { return fibresSiPM_U; }
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetFibresMapU() { return siPMFibres_U; }
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetSiPMmapV() { return fibresSiPM_V; }
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> GetFibresMapV() { return siPMFibres_V; }
    std::map<Int_t, float> GetSiPMPos_U() { return SiPMPos_U; }
    std::map<Int_t, float> GetSiPMPos_V() { return SiPMPos_V; }
    Float_t Get_SciFiActiveX() const { return fSciFiActiveX; }
    virtual void SiPMOverlap();
    virtual Bool_t ProcessHits(FairVolume* vol = 0);
    MtcDetPoint* AddHit(Int_t trackID,
                        Int_t detID,
                        TVector3 pos,
                        TVector3 mom,
                        Double_t time,
                        Double_t length,
                        Double_t eLoss,
                        Int_t pdgCode);

    virtual void Register();
    virtual void EndOfEvent();
    virtual TClonesArray* GetCollection(Int_t iColl) const;
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
    Double_t fWidth;
    Double_t fHeight;
    Double_t fSciFiActiveX;
    Double_t fSciFiActiveY;
    Double_t fSciFiBendingAngle;
    Double_t fIronThick;
    Double_t fSciFiThick;
    Double_t fScintThick;
    Int_t fLayers;
    Double_t fZCenter;
    Double_t fFieldY;
    Double_t fZEpoxyMat;
    Double_t fiberMatThick;
    Double_t fFiberLength;
    Double_t fFiberPitch;
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> fibresSiPM_U;   //! mapping of fibres to SiPM channels
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> siPMFibres_U;   //! inverse mapping
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> fibresSiPM_V;   //! mapping of fibres to SiPM channels
    std::map<Int_t, std::map<Int_t, std::array<float, 2>>> siPMFibres_V;   //! inverse mapping
    std::map<Int_t, float> SiPMPos_U, SiPMPos_V;                           //! local SiPM channel position
    /** container for data points */
    TClonesArray* fMTCDetectorPointCollection;

    MTCDetector(const MTCDetector&);
    MTCDetector& operator=(const MTCDetector&);
    Int_t InitMedium(const char* name);
    ClassDef(MTCDetector, 3)
};

#endif   // MTCDETECTOR_H_
