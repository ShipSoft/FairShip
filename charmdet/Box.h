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
    void AddEmulsionFilm(Double_t zposition, Int_t nreplica, TGeoVolume * volTarget, TGeoVolume * volEmulsionFilm, TGeoVolume * volEmulsionFilm2, TGeoVolume * volPlBase); 
  
    void SetTargetDesign(Bool_t Julytarget);
    void SetRunNumber(Int_t RunNumber);

    void SetBrickParam(Double_t BrX, Double_t BrY, Double_t BrZ, Double_t BrPackX, Double_t BrPackY, Double_t BrPackZ);
    void SetEmulsionParam(Double_t EmTh, Double_t EmX, Double_t EmY, Double_t PBTh,Double_t EPlW, Double_t PasSlabTh, Double_t AllPW);
    void SetPassiveComposition(Double_t Molblock1Z, Double_t Molblock2Z, Double_t Molblock3Z, Double_t Molblock4Z, Double_t Wblock1Z, Double_t Wblock2Z, Double_t Wblock3Z, Double_t Wblock3_5Z, Double_t Wblock4Z); 
    void SetPassiveSampling(Double_t Passive3mmZ, Double_t Passive2mmZ, Double_t Passive1mmZ);
 
    void SetTargetParam(Double_t TX, Double_t TY, Double_t TZ);
    void SetCoolingParam(Double_t CoolX, Double_t CoolY, Double_t CoolZ);
    void SetCoatingParam(Double_t CoatX, Double_t CoatY, Double_t CoatZ);

    void SetGapGeometry(Double_t distancePassive2ECC); //distance between passive and ECC
    
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
    
    ClassDef(Box,3)
    
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

    //new segmentation with gaps
    Double_t GapPostTargetThickness; //gap between target and T1 station

    //Target position
    Double_t zBoxPosition;
    
    Int_t InitMedium(const char* name);

    Bool_t fJulytarget; //Lead ECC vs SHiP ECC
    Bool_t ch1r6; //special case, CH1 run with a tungsten target
    //Number of the simulated run
    Int_t nrun;
    
    //attributes for the brick
    Double_t EmulsionThickness;
    Double_t EmulsionX;
    Double_t EmulsionY;
  
    //attributes for the new target configuration, to simulate SHiP target
    Double_t TargetX;
    Double_t TargetY;
    Double_t TargetZ;

    //target composition thicknesses (passive configuration)
    Double_t Mol1Z;
    Double_t Mol2Z;
    Double_t Mol3Z;
    Double_t Mol4Z;
    Double_t W1Z;
    Double_t W2Z;
    Double_t W3Z;
    Double_t W3_5Z; 
    Double_t W4Z;

    //target sampling components
    Double_t Pas3mmZ;
    Double_t Pas2mmZ;
    Double_t Pas1mmZ;

    Double_t distPas2ECC;
         
    //attributes for the cooling system( water )
    Double_t CoolingX;
    Double_t CoolingY;
    Double_t CoolingZ;
    
    //tantalum used for coating molybdenum and tungstenum slips
    Double_t CoatingX;
    Double_t CoatingY;
    Double_t CoatingZ;

    Double_t PlasticBaseThickness;
    Double_t PassiveSlabThickness;
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

