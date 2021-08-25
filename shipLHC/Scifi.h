#ifndef Scifi_H
#define Scifi_H


#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class ScifiPoint;
class FairVolume;
class TClonesArray;

class Scifi : public FairDetector
{
public:
    Scifi(const char* name, const Double_t xdim, Double_t ydim, const Double_t zdim, Bool_t Active, const char* Title = "Scifi");
    Scifi();
    virtual ~Scifi();
 
    
    /**      Create the detector geometry        */
    void ConstructGeometry();
    void SiPMOverlap();
    void SetScifiParam(Double_t xdim, Double_t ydim, Double_t zdim);
    void SetMatParam (Double_t scifimat_width, Double_t scifimat_length, Double_t scifimat_z, Double_t epoxymat_z, Double_t scifimat_gap);
    void SetFiberParam(Double_t fiber_length, Double_t scintcore_rmax, Double_t clad1_rmax, Double_t clad2_rmax);
    void SetFiberPosParam(Double_t horizontal_pitch, Double_t vertical_pitch, Double_t rowlong_offset, Double_t rowshort_offset);
    void SetPlaneParam(Double_t carbonfiber_z, Double_t honeycomb_z);
    void SetPlastBarParam(Double_t plastbar_x, Double_t plastbar_y, Double_t plastbar_z);
    void SetNFibers(Int_t nfibers_shortrow, Int_t nfibers_longrow, Int_t nfibers_z);
    void SetScifiSep(Double_t scifi_separation);
    void SetZOffset(Double_t offset_z);
    void SetNMats(Int_t nmats);
    void SetNScifi(Int_t nscifi);
    void SetNSiPMs(Int_t sipms);
    void SiPMParams(Double_t half_width, Double_t channel_width, Double_t charr_width, Double_t sipm_edge, Double_t charr_gap, Double_t simparr_width, Double_t sipm_diegap, Double_t nsipm_channels);

    /**      Initialization of the detector is done here    */
    virtual void Initialize();
    
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
    
    /**      This method is an example of how to add your own point
     *       of type muonPoint to the clones array
     */
    ScifiPoint* AddHit(Int_t trackID, Int_t detID,
                       TVector3 pos, TVector3 mom,
                       Double_t time, Double_t length,
                       Double_t eLoss, Int_t pdgCode);
    
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
    virtual void   PreTrack() {;}
    virtual void   BeginEvent() {;}
    
    
    Scifi(const Scifi&);
    Scifi& operator=(const Scifi&);
    
    ClassDef(Scifi,1)
    
private:
    
    /** Track information to be stored until the track leaves the
     active volume.
     */
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double32_t     fTime;              //!  time
    Double32_t     fLength;            //!  length
    Double32_t     fELoss;             //!  energy loss
    
    /** container for data points */
    TClonesArray*  fScifiPointCollection;
    
protected:
    
    Double_t fXDimension; //Dimension of Scifi planes
    Double_t fYDimension; //
    Double_t fZDimension; //
    
    Double_t fWidthScifiMat;  
    Double_t fLengthScifiMat;
    Double_t fZScifiMat;
    Double_t fZEpoxyMat; 
    Double_t fGapScifiMat; //Gap between mats

    Double_t fFiberLength;   //Fiber Dimensions
    Double_t fScintCore_rmax;  
    Double_t fClad1_rmin;    
    Double_t fClad1_rmax;    
    Double_t fClad2_rmin;    
    Double_t fClad2_rmax;    

    Double_t fHorPitch;   //Fiber position params
    Double_t fVertPitch;  //
    Double_t fOffsetRowS; //
    Double_t fOffsetRowL; //

    Double_t fZCarbonFiber; 
    Double_t fZHoneycomb;

    Double_t fXPlastBar; //Dimension of plastic bar
    Double_t fYPlastBar; //
    Double_t fZPlastBar; //

    Double_t fNFibers_Srow;   
    Double_t fNFibers_Lrow;     
    Double_t fNFibers_z;                 

    Double_t fSeparationBrick; //Separation between successive SciFi volumes
    Double_t fZOffset;
    
    Int_t fNMats;  //Number of mats in one SciFi plane
    Int_t fNScifi; //Number of Scifi walls
    Int_t fNSiPMs; //Number of SiPMs per SciFi plane

    Double_t fHalfWidth;    //Half width of the SiPM plane
    Double_t fWidthChannel; //One channel width 
    Double_t fCharr;        //Width of an array of 64 channels without gaps            
    Double_t fEdge;         //Edge at the left and right sides of the SiPM           
    Double_t fCharrGap;     //Gap between two charr
    Double_t fSipmArray;    //Width of 128 channels array with the gap
    Double_t fBigGap;       //Gap between two arrays                          
    Double_t fNSiPMChan;    //Number of channels in each SiPM
        
    Int_t InitMedium(const char* name);
    
};

#endif
