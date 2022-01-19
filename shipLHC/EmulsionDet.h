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
		Double_t time, Double_t length,Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom);
        
    virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 , Int_t offset) {;}
    virtual void   SetSpecialPhysicsCuts() {;}
    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack(){;}
    virtual void   BeginEvent() {;}

    /** Obtain info about brick position from detectorID**/
    void DecodeBrickID(Int_t detID, Int_t &NWall, Int_t &NRow, Int_t &NColumn, Int_t &NPlate);

    void SetConfPar(TString name, Float_t value){conf_floats[name]=value;}
    void SetConfPar(TString name, Int_t value){conf_ints[name]=value;}
    void SetConfPar(TString name, TString value){conf_strings[name]=value;}
    Float_t  GetConfParF(TString name){return conf_floats[name];} 
    Int_t       GetConfParI(TString name){return conf_ints[name];}
    TString  GetConfParS(TString name){return conf_strings[name];}

    EmulsionDet(const EmulsionDet&);
    EmulsionDet& operator=(const EmulsionDet&);
    
    ClassDef(EmulsionDet,5)
    
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
        /** configuration parameters **/
    std::map<TString,Float_t> conf_floats;
    std::map<TString,Int_t> conf_ints;
    std::map<TString,TString> conf_strings;

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

    Double_t TotalWallZDim; //including the aluminium border
    Double_t WallZBorder_offset; //border is asymmetric, 14 mm before, 4.5 mm after

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

    Int_t fPassiveOption; //passive option 1 passive all emulsions, 0 active all emulsions


    //TargetTrackers
    Double_t TTrackerZ;

   //Shift with respecto to floor in y
   Double_t ShiftY;
    //Shift with respect to center in x
    Double_t ShiftX;
    
    
    Int_t InitMedium(const char* name);
    
};

#endif

