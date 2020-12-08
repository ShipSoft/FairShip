//  
//EmulsionDet.h
//
// by A.Buonaura

#ifndef EmulsionDet_H
#define EmulsionDet_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class EmulsionDetPoint;
class FairVolume;
class TClonesArray;

class EmulsionDet : public FairDetector
{
public:
  EmulsionDet(const char* name, Bool_t Active, const char* Title = "EmulsionDet");
    EmulsionDet();
    virtual ~EmulsionDet();
    
    /**      Create the detector geometry        */
    void ConstructGeometry();  
    
    /** Other functions */
void SetTargetWallDimension(Double_t WallXDim, Double_t WallYDim, Double_t WallZDim);
    void SetDetectorDimension(Double_t xdim, Double_t ydim, Double_t zdim);
void SetEmulsionParam(Double_t EmTh, Double_t EmX, Double_t EmY, Double_t PBTh,Double_t EPlW, Double_t PassiveTh, Double_t AllPW);
    void SetBrickParam(Double_t BrX, Double_t BrY, Double_t BrZ, Double_t BrPackX, Double_t BrPackY,Double_t BrPackZ, Int_t number_of_plates_);
    void SetNumberBricks(Double_t col, Double_t row, Double_t wall);
    void SetTTzdimension(Double_t TTZ);
    void SetNumberTargets(Int_t target);
 void SetCenterZ(Double_t z);
   void SetDisplacement(Double_t x, Double_t y) {ShiftX=x; ShiftY=y;}
    
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
    
    /**      How to add your own point of type EmulsionDetPoint to the clones array */

    EmulsionDetPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
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
    
       
    EmulsionDet(const EmulsionDet&);
    EmulsionDet& operator=(const EmulsionDet&);
    
    ClassDef(EmulsionDet,2)
    
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
    TClonesArray*  fEmulsionDetPointCollection;
    
protected:
   
    Double_t XDimension; //dimension of the target box 
    Double_t YDimension;
    Double_t ZDimension; 

    Double_t fCenterZ;

    Int_t fNWall, fNRow, fNCol;
    Int_t fNTarget;
    Int_t number_of_plates; ////

    Double_t WallXDim; //dimension of the wall of bricks 
    Double_t WallYDim;
    Double_t WallZDim;

    Double_t EmulsionThickness;
    Double_t EmulsionX;
    Double_t EmulsionY;

    Double_t PlasticBaseThickness;
    Double_t PassiveThickness; //Tungsten plate thickness
    Double_t EmPlateWidth; // Z dimension of the emulsion plates = 2*EmulsionThickness+PlasticBaseThickness
    Double_t AllPlateWidth; //PlateZ + PassiveThickness


    Double_t BrickPackageX; //dimension of the brick package along X
    Double_t BrickPackageY; //dimension of the brick package along Y
    Double_t BrickPackageZ; //dimension of the brick package along Z

    Double_t BrickZ; //dimension of the brick + package along the Z axis
    Double_t BrickY;
    Double_t BrickX;


    //TargetTrackers
    Double_t TTrackerZ;

   //Shift with respecto to floor in y
   Double_t ShiftY;
    //Shift with respect to center in x
    Double_t ShiftX;
    
    
    Int_t InitMedium(const char* name);
    
};

#endif

