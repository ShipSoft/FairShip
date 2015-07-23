//
//  Target.h
//  
//
//  Created by Annarita Buonaura on 17/01/15.
//
//

#ifndef Target_H
#define Target_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class TargetPoint;
class FairVolume;
class TClonesArray;

class Target : public FairDetector
{
public:
    Target(const char* name, const Double_t zC, const Double_t GapTS, Bool_t Active, const char* Title = "NuTauTarget");
    Target();
    virtual ~Target();
    
    /**      Create the detector geometry        */
    void ConstructGeometry();
    
    void SetGoliathSizes(Double_t H, Double_t TS, Double_t LS, Double_t BasisH);
    void SetCoilParameters(Double_t CoilR, Double_t UpCoilH, Double_t LowCoilH, Double_t CoilD);
    
    void SetDetectorDimension(Double_t xdim, Double_t ydim, Double_t zdim);
    void SetEmulsionParam(Double_t EmTh, Double_t EmX, Double_t EmY, Double_t PBTh,Double_t EPlW, Double_t LeadTh, Double_t AllPW);
    void SetBrickParam(Double_t BrX, Double_t BrY, Double_t BrZ, Double_t BrPack);
    void SetCESParam(Double_t RohG, Double_t LayerCESW, Double_t CESW, Double_t CESPack);
    void SetCellParam(Double_t CellW);
    
    void SetTargetTrackerParam(Double_t TTX, Double_t TTY, Double_t TTZ);
    
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
    /*
	TargetPoint* AddHit(Int_t tr, Int_t detID,
                       TVector3 pos, TVector3 mom,
                       Double_t time, Double_t length,
                       Double_t eLoss, Int_t pdgCode,
		       Int_t EmTop, Int_t EmBot, Int_t EmCESTop, Int_t EmCESBot, Int_t TT, 
		       Int_t NPlate, Int_t NColumn, Int_t NRow, Int_t NWall, Int_t fMotherID, Int_t ftrackID);
*/

	TargetPoint* AddHit(Int_t trackID, Int_t detID,
                       TVector3 pos, TVector3 mom,
                       Double_t time, Double_t length,
                       Double_t eLoss, Int_t pdgCode,
		       Int_t EmTop, Int_t EmBot, Int_t EmCESTop, Int_t EmCESBot, Int_t TT, 
		       Int_t NPlate, Int_t NColumn, Int_t NRow, Int_t NWall);

    
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
    
    
    Target(const Target&);
    Target& operator=(const Target&);
    
    ClassDef(Target,1)
    
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
    TClonesArray*  fTargetPointCollection;
    
protected:
    
    //Goliath
    
    Double_t Height;
    Double_t zCenter;
    Double_t LongitudinalSize;
    Double_t TransversalSize;
    Double_t GapFromTSpectro;
    Double_t CoilRadius;
    Double_t UpCoilHeight;
    Double_t LowCoilHeight;
    Double_t CoilDistance;
    Double_t BasisHeight;
    
    //Bricks
    
    Double_t XDimension; //dimension of the target box (= 2 x 2 x 1) m^3
    Double_t YDimension;
    Double_t ZDimension;
    
    Double_t EmulsionThickness;
    Double_t EmulsionX;
    Double_t EmulsionY;
    
    Double_t PlasticBaseThickness;
    Double_t LeadThickness;
    Double_t EmPlateWidth; // Z dimension of the emulsion plates = 2*EmulsionThickness+PlasticBaseThickness
    Double_t AllPlateWidth; //PlateZ + LeadThickness

    Double_t BrickPackageZ; //dimension of the brick package along Z
    Double_t CESPackageZ; //dimension of the CES package along Z
    
    Double_t BrickZ; //dimension of the brick + package along the Z axis
    Double_t BrickY;
    Double_t BrickX;
 
    Double_t RohacellGap; //dimension of the Rohacell Gap in CES along Z axis
    Double_t LayerCESWidth;
    Double_t CESWidth; //dimension of the CES along Z axis
    
    Double_t CellWidth; //dimension of Brick + CES along Z axis
    
    //TargetTrackers
    Double_t TTrackerX;
    Double_t TTrackerY;
    Double_t TTrackerZ;

    
    Int_t InitMedium(const char* name);
    
};

#endif

