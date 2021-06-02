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
    Scifi(const char* name, const Double_t DX, Double_t DY, const Double_t DZ, Bool_t Active, const char* Title = "Brick");
    Scifi();
    virtual ~Scifi();
 
    
    /**      Create the detector geometry        */
    void ConstructGeometry();
    void SetTotZDimension(Double_t Zdim){FullDetZdim = Zdim;}
    void SetDetectorDimension(Double_t xdim, Double_t ydim, Double_t zdim);
    void SetScifiNplanes(Int_t n) {fNplanes = n;}
    void SetGapBrick(Double_t d) {DeltaZ = d;}

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
    
    Double_t XDimension; // Dimension of Scifi planes
    Double_t YDimension; //
    Double_t ZDimension; //
    Double_t FullDetZdim; //Z Dimension whole detector 
    Double_t DeltaZ; //Distance between each target tracker plane (= Brick)
    Int_t fNplanes;
        
    Int_t InitMedium(const char* name);
    
};

#endif
