#ifndef UPSTREAMTAGGER_H
#define UPSTREAMTAGGER_H

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"

class UpstreamTaggerPoint;
class FairVolume;
class TClonesArray;


class UpstreamTagger: public FairDetector
{
  
  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    UpstreamTagger(const char* Name, Bool_t Active);

    /** default constructor */
    UpstreamTagger();

    /** destructor */
    virtual ~UpstreamTagger();

    /** Initialization of the detector is done here */
    virtual void   Initialize();

    /**   this method is called for each step during simulation
     *    (see FairMCApplication::Stepping())
    */
    virtual Bool_t ProcessHits( FairVolume* v=0);

    /**       Registers the produced collections in FAIRRootManager. */
    virtual void Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const;

    /** has to be called after each event to reset the containers */
    virtual void Reset();

    /** Sets detector position and sizes */
    void SetZposition(Double_t z) {det_zPos = z;}
    void SetSizeX_Glass(Double_t xg) {det_xGlassPos = xg;}
    void SetSizeY_Glass(Double_t yg) {det_yGlassPos = yg;}
    void SetSizeZ_Glass(Double_t zg) {det_zGlassPos = zg;}
    void SetSizeX_Glass_Border(Double_t xgB) {det_xGlassBorderPos = xgB;}
    void SetSizeY_Glass_Border(Double_t ygB) {det_yGlassBorderPos = ygB;}
    void SetSizeZ_Glass_Border(Double_t zgB) {det_zGlassBorderPos = zgB;}
    void SetSizeX_PMMA(Double_t xpmma) {det_xPMMAPos = xpmma;}
    void SetSizeY_PMMA(Double_t ypmma) {det_yPMMAPos = ypmma;}
    void SetSizeZ_PMMA(Double_t zpmma) {det_zPMMAPos = zpmma;}
    void SetSizeDX_PMMA(Double_t dxpmma) {det_dxPMMAPos = dxpmma;}
    void SetSizeDY_PMMA(Double_t dypmma) {det_dyPMMAPos = dypmma;}
    void SetSizeDZ_PMMA(Double_t dzpmma) {det_dzPMMAPos = dzpmma;}
    void SetSizeX_FreonSF6(Double_t xfSF6) {det_xFreonSF6Pos = xfSF6;}
    void SetSizeY_FreonSF6(Double_t yfSF6) {det_yFreonSF6Pos = yfSF6;}
    void SetSizeZ_FreonSF6(Double_t zfSF6) {det_zFreonSF6Pos = zfSF6;}
    void SetSizeX_FreonSF6_2(Double_t xfSF6_2) {det_xFreonSF6Pos_2 = xfSF6_2;}
    void SetSizeY_FreonSF6_2(Double_t yfSF6_2) {det_yFreonSF6Pos_2 = yfSF6_2;}
    void SetSizeZ_FreonSF6_2(Double_t zfSF6_2) {det_zFreonSF6Pos_2 = zfSF6_2;}
    void SetSizeX_FR4(Double_t xf) {det_xFR4Pos = xf;}
    void SetSizeY_FR4(Double_t yf) {det_yFR4Pos = yf;}
    void SetSizeZ_FR4(Double_t zf) {det_zFR4Pos = zf;}
    void SetSizeX_Al(Double_t xal) {det_xAlPos = xal;}
    void SetSizeY_Al(Double_t yal) {det_yAlPos = yal;}
    void SetSizeZ_Al(Double_t zal) {det_zAlPos = zal;}
    void SetSizeDX_Al(Double_t dxal) {det_dxAlPos = dxal;}
    void SetSizeDY_Al(Double_t dyal) {det_dyAlPos = dyal;}
    void SetSizeDZ_Al(Double_t dzal) {det_dzAlPos = dzal;}
    void SetSizeX_Air(Double_t xair) {det_xAirPos = xair;}
    void SetSizeY_Air(Double_t yair) {det_yAirPos = yair;}
    void SetSizeZ_Air(Double_t zair) {det_zAirPos = zair;}
    void SetSizeX_Strip(Double_t xstrip) {det_xStripPos = xstrip;}
    void SetSizeY_Strip(Double_t ystrip) {det_yStripPos = ystrip;}
    void SetSizeX_Strip64(Double_t xstrip64) {det_xStripPos64 = xstrip64;}
    void SetSizeY_Strip64(Double_t ystrip64) {det_yStripPos64 = ystrip64;}
    void SetSizeZ_Strip(Double_t zstrip) {det_zStripPos = zstrip;}
    

    /**  Create the detector geometry */
    void ConstructGeometry();

    /**      This method is an example of how to add your own point
     *       of type TimeRpcPoint to the clones array
    */
    UpstreamTaggerPoint* AddHit(Int_t trackID, Int_t detID,
			 TVector3 pos, TVector3 mom,
			 Double_t time, Double_t length,
			 Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom);

    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack() {;}
    virtual void   BeginEvent() {;}
   
    Double_t module[11][3];
    
  private:

    /** Track information to be stored until the track leaves the active volume.*/
    Int_t          fTrackID;            //!  track index
    Int_t          fVolumeID;           //!  volume id
    TLorentzVector fPos;                //!  position at entrance
    TLorentzVector fMom;                //!  momentum at entrance
    Double_t       fTime;               //!  time
    Double_t       fLength;             //!  length
    Double_t       fELoss;              //!  energy loss

    /** Detector parameters.*/

    Double_t     det_zPos;     //!  z-position of veto station
    Double_t     det_xGlassPos;     //!  x-size of Active Glass plates 
    Double_t     det_yGlassPos;     //!  y-size of Active Glass plates
    Double_t     det_zGlassPos;     //!  z-size of Active Glass plates
    
    Double_t     det_xGlassBorderPos;     //!  x-size of Inactive Glass plates
    Double_t     det_yGlassBorderPos;     //!  y-size of Inactive Glass plates
    Double_t     det_zGlassBorderPos;     //!  z-size of Inactive Glass plates

    Double_t     det_xPMMAPos;     //!  x-size of PMMA box
    Double_t     det_yPMMAPos;     //!  y-size of PMMA box
    Double_t     det_zPMMAPos;     //!  z-size of PMMA box

    Double_t     det_dxPMMAPos;     //!  x-thickness of PMMA box
    Double_t     det_dyPMMAPos;     //!  y-thickness of PMMA box
    Double_t     det_dzPMMAPos;     //!  z-thickness of PMMA box

    Double_t     det_xFreonSF6Pos;     //!  x-size of gas gap
    Double_t     det_yFreonSF6Pos;     //!  y-size of gas gap
    Double_t     det_zFreonSF6Pos;     //!  z-size of gas gap

    Double_t     det_xFreonSF6Pos_2;     //!  x-size of gas gap
    Double_t     det_yFreonSF6Pos_2;     //!  y-size of gas gap
    Double_t     det_zFreonSF6Pos_2;     //!  z-size of gas gap

    Double_t     det_xFR4Pos;     //!  x-size of FR4 box
    Double_t     det_yFR4Pos;     //!  y-size of FR4 box
    Double_t     det_zFR4Pos;     //!  z-size of FR4 box

    Double_t     det_xAlPos;     //!  x-size of Aluminium box
    Double_t     det_yAlPos;     //!  y-size of Aluminium box
    Double_t     det_zAlPos;     //!  z-size of Aluminium box

    Double_t     det_dxAlPos;     //!  x-thickness of Aluminium box
    Double_t     det_dyAlPos;     //!  y-thickness of Aluminium box
    Double_t     det_dzAlPos;     //!  z-thickness of Aluminium box
    
    Double_t     det_xAirPos;     //!  x-size of Aluminium box
    Double_t     det_yAirPos;     //!  y-size of Aluminium box
    Double_t     det_zAirPos;     //!  z-size of Aluminium box
    
    Double_t     det_xStripPos64;     //!  x-size of Strip for modules with 64 strips
    Double_t     det_yStripPos64;     //!  y-size of Strip for modules with 64 strips
    Double_t     det_xStripPos;     //!  x-size of Strip for modules with 32 strips
    Double_t     det_yStripPos;     //!  y-size of Strip for modules with 32 strips
    Double_t     det_zStripPos;     //!  z-size of Strip
    
    Double_t xbox_fulldet = 233.4; //cm 
    Double_t ybox_fulldet = 507; 
    Double_t zbox_fulldet = 17.0024;
    Double_t z_space_layers = 0.2;  
    Double_t extra_y = 6.5; 
    
    TGeoVolume* UpstreamTagger_fulldet; // Timing_detector_1 object
   
    /** container for data points */
    TClonesArray* fUpstreamTaggerPointCollection;

    UpstreamTagger(const UpstreamTagger&);
    UpstreamTagger& operator=(const UpstreamTagger&);
    Int_t InitMedium(const char* name);


    ClassDef(UpstreamTagger,1)
};

#endif //UPSTREAMTAGGER_H
