//  
//Box.h
//
//

#ifndef Box_H
#define Box_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class BoxPoint;
class FairVolume;
class TClonesArray;

class Box : public FairDetector
{
public:
  Box(const char* name, const Double_t BX, const Double_t BY, const Double_t BZ, const Double_t zBox, Bool_t Active, const char* Title = "Box");
    Box();
    virtual ~Box();
    
    /**      Create the detector geometry        */
    void ConstructGeometry();  

    void SetPassiveParam(Double_t PX, Double_t PY, Double_t Pz);
    void SetBrickParam(Double_t BrX, Double_t BrY, Double_t BrZ, Double_t BrPackX, Double_t BrPackY, Double_t BrPackZ);
    void SetEmulsionParam(Double_t EmTh, Double_t EmX, Double_t EmY, Double_t PBTh,Double_t EPlW, Double_t MolybdenumTh, Double_t AllPW);
  
    void SetTargetParam(Double_t TX, Double_t TY, Double_t TZ);
    void SetCoolingParam(Double_t CoolX, Double_t CoolY, Double_t CoolZ);
    void SetCoatingParam(Double_t CoatX, Double_t CoatY, Double_t CoatZ);

   
    
    /**      Initialization of the detector is done here    */
    virtual void Initialize();
    
    /**  Method called for each step during simulation (see FairMCApplication::Stepping()) */
    virtual Bool_t ProcessHits( FairVolume* v=0);
    
    /**       Registers the produced collections in FAIRRootManager.     */
    virtual void   Register();
    
    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const ;
    
    /**      has to be called after each event to reset the containers      */
    virtual void   Reset();
    
    /**      How to add your own point of type BoxPoint to the clones array */

    BoxPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
		     Double_t time, Double_t length, Double_t eLoss, Int_t pdgCode);
    
        
    virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 , Int_t offset) {;}
    virtual void   SetSpecialPhysicsCuts() {;}
    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack() {;}
    virtual void   BeginEvent() {;}
    
       
    Box(const Box&);
    Box& operator=(const Box&);
    
    ClassDef(Box,1)
    
private:
    
    /** Track information to be stored until the track leaves the active volume. */
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double32_t     fTime;              //!  time
    Double32_t     fLength;            //!  length
    Double32_t     fELoss;             //!  energy loss
    
    /** container for data points */
    TClonesArray*  fBoxPointCollection;
    
protected:

 

    //Target
    
    Double_t   BoxX;
    Double_t   BoxY;
    Double_t   BoxZ;
    Double_t zBoxPosition;
    
    Int_t InitMedium(const char* name);


    //attributes for an additional pre-target
    Double_t PassiveX;
    Double_t PassiveY;
    Double_t PassiveZ;
    
    //attributes for the brick
    Double_t EmulsionThickness;
    Double_t EmulsionX;
    Double_t EmulsionY;
  
    //attributes for the new target configuration, to simulate SHiP target
    Double_t TargetX;
    Double_t TargetY;
    Double_t TargetZ;
         
    //attributes for the cooling system( water )
    Double_t CoolingX;
    Double_t CoolingY;
    Double_t CoolingZ;
    
    //tantalum used for coating molybdenum and tungstenum slips
    Double_t CoatingX;
    Double_t CoatingY;
    Double_t CoatingZ;

    Double_t PlasticBaseThickness;
    Double_t MolybdenumThickness;
    Double_t EmPlateWidth; // Z dimension of the emulsion plates = 2*EmulsionThickness+PlasticBaseThickness
    Double_t AllPlateWidth; //PlateZ + LeadThickness


    Double_t BrickPackageX; //dimension of the brick package along X
    Double_t BrickPackageY; //dimension of the brick package along Y
    Double_t BrickPackageZ; //dimension of the brick package along Z
    Double_t BrickZ; //dimension of the brick + package along the Z axis
    Double_t BrickY;
    Double_t BrickX;
};

#endif

