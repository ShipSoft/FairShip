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
    void SetScifiParam(Double_t xdim, Double_t ydim, Double_t zdim);
    void SetMatParam (Double_t scifimat_width, Double_t scifimat_length, Double_t scifimat_z, Double_t scifimat_gap);
    void SetPlaneParam(Double_t carbonfiber_z, Double_t honeycomb_z);
    void SetPlastBarParam(Double_t plastbar_x, Double_t plastbar_y, Double_t plastbar_z);
    void SetScifiSep(Double_t scifi_separation);
    void SetZOffset(Double_t offset_z);
    void SetNMats(Int_t nmats);
    void SetNScifi(Int_t nscifi);
    void SetNSiPMs(Int_t sipms);

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
    Double_t fGapScifiMat; //Gap between mats

    Double_t fZCarbonFiber; 
    Double_t fZHoneycomb;

    Double_t fXPlastBar; //Dimension of plastic bar
    Double_t fYPlastBar; //
    Double_t fZPlastBar; //

    Double_t fSeparationBrick; //Separation between successive SciFi volumes
    Double_t fZOffset;
    
    Int_t fNMats;  //Number of mats in one SciFi plane
    Int_t fNScifi; //Number of Scifi walls
    Int_t fNSiPMs; //Number of SiPMs per SciFi plane
        
    Int_t InitMedium(const char* name);
    
};

#endif
