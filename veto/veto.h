#ifndef VETO_H
#define VETO_H

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "TGeoVolume.h"

#include <map>

class vetoPoint;
class FairVolume;
class TClonesArray;

class veto: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    veto(const char* Name, Bool_t Active);

    /**      default constructor    */
    veto();

    /**       destructor     */
    virtual ~veto();

    /**      Initialization of the detector is done here    */
    virtual void   Initialize();

    /**       this method is called for each step during simulation
     *       (see FairMCApplication::Stepping())
    */
    virtual Bool_t ProcessHits( FairVolume* v=0);

    /**       Registers the produced collections in FAIRRootManager.     */
    virtual void   Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const ;

    /**      has to be called after each event to reset the containers      */
    virtual void   Reset();

    void SetFastMuon() {fFastMuon=true;}  // kill all tracks except of muons
    void SetFollowMuon() {fFollowMuon=true;}  // make muon shield active to follow muons

    /**      Create the detector geometry        */
    void ConstructGeometry();

    void SetZpositions(Float_t z0, Float_t z1, Float_t z2, Float_t z3, Float_t z4, Int_t c);
    void SetTubZpositions(Float_t z1, Float_t z2, Float_t z3, Float_t z4, Float_t z5, Float_t z6);
    void SetTublengths(Float_t l1, Float_t l2, Float_t l3, Float_t l4, Float_t l5, Float_t l6);
    void SetB(Float_t b) {fBtube=b;}
    void SetFloorHeight(Float_t a,Float_t b) {floorHeightA=a;floorHeightB=b;}
    void SetXYstart(Float_t b, Float_t fx, Float_t c, Float_t fy) {fXstart=b; zFocusX=fx; fYstart=c; zFocusY=fy;}
    void SetVesselStructure(Float_t a,Float_t b,Float_t c,TString d,Float_t l,TString e,TString f,TString v,Float_t r, TString rm) {f_InnerSupportThickness=a;
      f_VetoThickness=b;f_OuterSupportThickness=c;supportMedIn_name=d;f_LidThickness=l;vetoMed_name=e;supportMedOut_name=f;decayVolumeMed_name=v;
     f_RibThickness=r;ribMed_name=rm;}

    /**      This method is an example of how to add your own point
     *       of type vetoPoint to the clones array
    */
    vetoPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom);

    /** The following methods can be implemented if you need to make
     *  any optional action in your detector during the transport.
    */

    virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 ,
                               Int_t offset) {;}
    virtual void   SetSpecialPhysicsCuts() {;}
    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack();
    virtual void   BeginEvent() {;}

    inline void SetUseSupport(Int_t use=1) {fUseSupport=use;}
    inline Int_t GetUseSupport() const {return fUseSupport;}

    inline void SetPlasticVeto(Int_t plastic=1) {fPlasticVeto=plastic;}
    inline Int_t GetPlasticVeto() const {return fPlasticVeto;}

    inline void SetLiquidVeto(Int_t liquid=1) {fLiquidVeto=liquid;}
    inline Int_t GetLiquidVeto() const {return fLiquidVeto;}

  private:

    /** Track information to be stored until the track leaves the
    active volume.
    */
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Float_t     fTime;              //!  time
    Float_t     fLength;            //!  length
    Float_t     fELoss;             //!  energy loss
    Float_t     fT0z;               //!  z-position of veto station
    Float_t     fT1z;               //!  z-position of tracking station 1
    Float_t     fT2z;               //!  z-position of tracking station 2
    Float_t     fT3z;               //!  z-position of tracking station 3
    Float_t     fT4z;               //!  z-position of tracking station 4
    Int_t          fDesign;            //!  1: cylindrical with basic tracking chambers, 
                                       //   2: conical with basic tracking chambers, but no trscking chamber at entrance 
                                       //   3: cylindrical, no tracking chambers defined but sensitive walls, strawchambers separated
                                       //   4: design used for TP, smaller upstream part in x
                                       //   5: optimized design, changed to trapezoidal shape
    Bool_t     fFastMuon, fFollowMuon;
    Float_t fTub1z;
    Float_t fTub2z;
    Float_t fTub3z;
    Float_t fTub4z;
    Float_t fTub5z;
    Float_t fTub6z;
    Float_t fTub1length;
    Float_t fTub2length;
    Float_t fTub3length;
    Float_t fTub4length;
    Float_t fTub5length;
    Float_t fTub6length;
    Float_t f_InnerSupportThickness;
    Float_t f_PhiRibsThickness;
    Float_t f_OuterSupportThickness;
    Float_t f_LidThickness;
    Float_t f_VetoThickness;
    Float_t f_RibThickness;
    Float_t fBtube;
    Float_t ws;
    TString vetoMed_name;         //! medium of veto counter, liquid or plastic scintillator
    TString supportMedIn_name;    //! medium of support structure, iron, balloon
    TString supportMedOut_name;   //! medium of support structure, aluminium, balloon
    TString decayVolumeMed_name;  //! medium of decay volume, vacuum/air/helium
    TString ribMed_name;          //! medium of rib support structure
    TString phi_ribMed_name;      //! medium of phi_ribs structure separating  the LiSc segments in XY plane 
    TGeoMedium *vetoMed;    //! 
    TGeoMedium *supportMedIn; //! 
    TGeoMedium *supportMedOut; //! 
    TGeoMedium *decayVolumeMed; //! 
    TGeoMedium *ribVolumeMed; //! 
    TGeoMedium *ribMed; //!
    TGeoMedium *phi_ribMed; //!

    Float_t fXstart,fYstart; // horizontal/vertical width at start of tank
    Float_t zFocusX,zFocusY; // focus points for conical design
    Float_t floorHeightA,floorHeightB; // height of floor

    Int_t fUseSupport;
    Int_t fPlasticVeto;
    Int_t fLiquidVeto;
    /** container for data points */
    TClonesArray*  fvetoPointCollection;

    veto(const veto&);
    veto& operator=(const veto&);
    Int_t InitMedium(const char* name);
    TGeoVolume* GeoTrapezoidNew(TString xname,Double_t thick,Double_t wz,Double_t wX_start,Double_t wX_end,Double_t wY_start,Double_t wY_end,Int_t color,TGeoMedium *material,Bool_t sens);
    void AddBlock(TGeoVolumeAssembly *tInnerWall,TGeoVolumeAssembly *tOuterWall,TGeoVolumeAssembly *tLongitRib,TGeoVolumeAssembly *tVerticalRib,TGeoVolumeAssembly *ttLiSc,  int& liScCounter,
                     TString blockName , int nx, int ny,
		  double z1, double z2 , double Zshift, double dist, double distC,
		    double wallThick, double liscThick1, double liscThick2,double ribThick);
    
    TGeoVolumeAssembly* GeoCornerRib(TString xname, double ribThick, double lt1,double lt2 , double dz, double slopeX, double slopeY,Int_t color, TGeoMedium *material, Bool_t sens);
   int makeId(double z,double x, double y);
    
        TGeoVolume* GeoSideObj(TString xname, double dz,
			     double a1, double b1,double a2, double b2,double dA, double dB,
				Int_t color, TGeoMedium *material, Bool_t sens);
    TGeoVolume* GeoCornerLiSc1(TString xname, double dz,bool isClockwise,
			     double a, double b1,double b2, double dA, double dB,
				Int_t color, TGeoMedium *material, Bool_t sens);
    TGeoVolume* GeoCornerLiSc2(TString xname, double dz,bool isClockwise,
			     double a, double b1,double b2, double dA, double dB,
				Int_t color, TGeoMedium *material, Bool_t sens);


    TGeoVolume* MakeSegments(Double_t dz,Double_t dx_start,Double_t dy,Double_t slopex,Double_t slopey,Double_t floorHeight);
    TGeoVolume* MakeMagnetSegment(Int_t seg);
    TGeoVolume* MakeLidSegments(Int_t seg,Double_t dx,Double_t dy);

    
    Int_t fDeltaCpy;	//Delta in copy number for solid plastic veto
    std::map<Int_t, TVector3> fCenters; //! Map of copy number to center of tiles 

    // Return copy number for solid plastic scitillator veto
    inline Int_t GetCopyNumber(Int_t iz, Int_t iplank, Int_t region) 
    { return (iz*1000+iplank)*10+region+fDeltaCpy; }

    // Add center of volume and its dx, dy and dz (currently dummy) to a map for futher export 
    void InnerAddToMap(Int_t ncpy, Double_t x, Double_t y, Double_t z, Double_t dx=-1111, Double_t dy=-1111, Double_t dz=-1111);


    ClassDef(veto, 9)
};

#endif //VETO_H
