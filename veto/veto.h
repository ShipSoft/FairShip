#ifndef VETO_VETO_H_
#define VETO_VETO_H_

#include "FairDetector.h"
#include "TGeoVolume.h"
#include "TLorentzVector.h"
#include "TVector3.h"

#include <map>

class vetoPoint;
class FairVolume;
class TClonesArray;

class veto : public FairDetector
{

  public:
    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
     */

    veto();

    /**       destructor     */
    virtual ~veto();

    /**      Initialization of the detector is done here    */
    virtual void Initialize();

    /**       this method is called for each step during simulation
     *       (see FairMCApplication::Stepping())
     */
    virtual Bool_t ProcessHits(FairVolume* v = 0);

    /**       Registers the produced collections in FAIRRootManager.     */
    virtual void Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const;

    /**      has to be called after each event to reset the containers      */
    virtual void Reset();

    void SetFastMuon() { fFastMuon = true; }       // kill all tracks except of muons
    void SetFollowMuon() { fFollowMuon = true; }   // make muon shield active to follow muons
    void SetVesselDimensions(Float_t x1, Float_t x2, Float_t y1, Float_t y2, Float_t vesselstart)
    {
        VetoStartInnerX = x1;
        VetoEndInnerX = x2;
        VetoStartInnerY = y1;
        VetoEndInnerY = y2;
        zStartDecayVol = vesselstart;
    }

    /**      Create the detector geometry        */
    void ConstructGeometry();

    void SetVesselStructure(Float_t a,
                            Float_t b,
                            Float_t c,
                            TString d,
                            Float_t l,
                            TString e,
                            TString f,
                            TString v,
                            Float_t r)
    {
        f_InnerSupportThickness = a;
        f_VetoThickness = b;
        f_OuterSupportThickness = c;
        supportMedIn_name = d;
        f_LidThickness = l;
        vetoMed_name = e;
        supportMedOut_name = f;
        decayVolumeMed_name = v;
        f_RibThickness = r;
    }

    /**      This method is an example of how to add your own point
     *       of type vetoPoint to the clones array
     */
    vetoPoint* AddHit(Int_t trackID,
                      Int_t detID,
                      TVector3 pos,
                      TVector3 mom,
                      Double_t time,
                      Double_t length,
                      Double_t eLoss,
                      Int_t pdgcode,
                      TVector3 Lpos,
                      TVector3 Lmom);

    /** The following methods can be implemented if you need to make
     *  any optional action in your detector during the transport.
     */

    virtual void CopyClones(TClonesArray* cl1, TClonesArray* cl2, Int_t offset) { ; }
    virtual void SetSpecialPhysicsCuts() { ; }
    virtual void EndOfEvent();
    virtual void FinishPrimary() { ; }
    virtual void FinishRun() { ; }
    virtual void BeginPrimary() { ; }
    virtual void PostTrack() { ; }
    virtual void PreTrack();
    virtual void BeginEvent() { ; }

    inline void SetUseSupport(Int_t use = 1) { fUseSupport = use; }
    inline Int_t GetUseSupport() const { return fUseSupport; }

    inline void SetPlasticVeto(Int_t plastic = 1) { fPlasticVeto = plastic; }
    inline Int_t GetPlasticVeto() const { return fPlasticVeto; }

    inline void SetLiquidVeto(Int_t liquid = 1) { fLiquidVeto = liquid; }
    inline Int_t GetLiquidVeto() const { return fLiquidVeto; }

  private:
    /** Track information to be stored until the track leaves the
    active volume.
    */
    Int_t fTrackID;        //!  track index
    Int_t fVolumeID;       //!  volume id
    TLorentzVector fPos;   //!  position at entrance
    TLorentzVector fMom;   //!  momentum at entrance
    Float_t fTime;         //!  time
    Float_t fLength;       //!  length
    Float_t fELoss;        //!  energy loss
    Float_t fT0z;          //!  z-position of veto station
    Float_t fT1z;          //!  z-position of tracking station 1
    Float_t fT2z;          //!  z-position of tracking station 2
    Float_t fT3z;          //!  z-position of tracking station 3
    Float_t fT4z;          //!  z-position of tracking station 4
    // Int_t          fDesign;            //!  1: cylindrical with basic tracking chambers,
    //    2: conical with basic tracking chambers, but no trscking chamber at entrance
    //    3: cylindrical, no tracking chambers defined but sensitive walls, strawchambers separated
    //    4: design used for TP, smaller upstream part in x
    //    5: optimized design, changed to trapezoidal shape
    // design version 1) Helium Balloon, 2) DV+wSBT to be added.
    Bool_t fFastMuon, fFollowMuon;
    Float_t fTub1z;
    Float_t fTub2z;
    Float_t fTub3z;
    Float_t fTub4z;
    Float_t fTub5z;
    Float_t fTub6z;
    Float_t fTub1length;
    Float_t fTub2length;
    Float_t fTub3length;
    Float_t fTub6length;
    Float_t f_InnerSupportThickness;
    Float_t f_OuterSupportThickness;
    Float_t f_LidThickness;
    Float_t f_VetoThickness;
    Float_t f_RibThickness;
    Float_t fBtube;
    TString vetoMed_name;          //! medium of veto counter, liquid or plastic scintillator
    TString supportMedIn_name;     //! medium of support structure, iron, balloon
    TString supportMedOut_name;    //! medium of support structure, aluminium, balloon
    TString decayVolumeMed_name;   //! medium of decay volume, vacuum/air/helium
    TGeoMedium* vetoMed;           //!
    TGeoMedium* supportMedIn;      //!
    TGeoMedium* supportMedOut;     //!
    TGeoMedium* decayVolumeMed;    //!

    Float_t fXstart, fYstart;             // horizontal/vertical width at start of tank
    Float_t zFocusX, zFocusY;             // focus points for conical design
    Float_t floorHeightA, floorHeightB;   // height of floor

    Float_t VetoStartInnerX;
    Float_t VetoStartInnerY;
    Float_t VetoEndInnerX;
    Float_t VetoEndInnerY;
    Float_t zStartDecayVol;

    Int_t fUseSupport;
    Int_t fPlasticVeto;
    Int_t fLiquidVeto;
    /** container for data points */
    TClonesArray* fvetoPointCollection;

    veto(const veto&);
    veto& operator=(const veto&);
    Int_t InitMedium(const char* name);
    TGeoVolume* GeoTrapezoid(TString xname,
                             Double_t wz,
                             Double_t wX_start,
                             Double_t wX_end,
                             Double_t wY_start,
                             Double_t wY_end,
                             Int_t color,
                             TGeoMedium* material,
                             Bool_t sens);
    TGeoVolume* GeoTrapezoidHollow(TString xname,
                                   Double_t thick,
                                   Double_t wz,
                                   Double_t wX_start,
                                   Double_t wX_end,
                                   Double_t wY_start,
                                   Double_t wY_end,
                                   Int_t color,
                                   TGeoMedium* material,
                                   Bool_t sens);

    void AddBlock(TGeoVolumeAssembly* tInnerWall,
                  TGeoVolumeAssembly* tDecayVacuum,
                  TGeoVolumeAssembly* tOuterWall,
                  TGeoVolumeAssembly* tLongitRib,
                  TGeoVolumeAssembly* tVerticalRib,
                  TGeoVolumeAssembly* ttLiSc,
                  int& liScCounter,
                  int blockNr,
                  int nx,
                  int ny,
                  double z1,
                  double z2,
                  double Zshift,
                  double dist,
                  double wallThick,
                  double liscThick1,
                  double liscThick2,
                  double ribThick);

    TGeoVolumeAssembly* GeoCornerRib(TString xname,
                                     double ribThick,
                                     double lt1,
                                     double lt2,
                                     double dz,
                                     double slopeX,
                                     double slopeY,
                                     Int_t color,
                                     TGeoMedium* material,
                                     Bool_t sens);
    int makeId(double z, double x, double y);
    int liscId(TString ShapeTypeName, int blockNr, int Zlayer, int number, int position);
    double wx(double z);
    double wy(double z);

    TGeoVolume* GeoSideObj(TString xname,
                           double dz,
                           double a1,
                           double b1,
                           double a2,
                           double b2,
                           double dA,
                           double dB,
                           Int_t color,
                           TGeoMedium* material,
                           Bool_t sens);
    TGeoVolume* GeoCornerLiSc1(TString xname,
                               double dz,
                               bool isClockwise,
                               double a1,
                               double a2,
                               double b1,
                               double b2,
                               double dA,
                               double dB,
                               Int_t color,
                               TGeoMedium* material,
                               Bool_t sens);
    TGeoVolume* GeoCornerLiSc2(TString xname,
                               double dz,
                               bool isClockwise,
                               double a1,
                               double a2,
                               double b1,
                               double b2,
                               double dA,
                               double dB,
                               Int_t color,
                               TGeoMedium* material,
                               Bool_t sens);

    TGeoVolume* MakeSegments();
    TGeoVolume* MakeLidSegments(Int_t seg, Double_t dx, Double_t dy);

    ClassDef(veto, 1)
};

#endif   // VETO_VETO_H_
