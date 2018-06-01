#ifndef HPT_H
#define HPT_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"                  // for FairDetector

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class HptPoint;
class FairVolume;
class TClonesArray;

class Hpt:public FairDetector
{
  public:
  Hpt(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ,Bool_t Active, const char* Title="HighPrecisionTrackers");
    Hpt();
    virtual ~Hpt();
      
    void ConstructGeometry();
    void SetZsize(const Double_t Mudetsize);
    void SetConcreteBaseDim(Double_t X, Double_t Y, Double_t Z);
    
    void SetDesign(Int_t Design);
    //methods for design 3 
    void SetDistanceHPTs(Double_t dd);       
    void SetHPTNumber(Int_t nHPT);
    void SetSurroundingDetHeight(Double_t height);
    void GetMagnetGeometry(Double_t EmuzC, Double_t EmuY);
    void GetNumberofTargets(Int_t ntarget);
    //
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
    HptPoint* AddHit(Int_t trackID, Int_t detID,
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

    void DecodeVolumeID(Int_t detID,int &nHPT);
    
private:
    
    /** Track information to be stored until the track leaves the
     active volume.
     */
    Int_t          fTrackID;           //!  track index
    Int_t          fPdgCode;           //!  pdg code
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double32_t     fTime;              //!  time
    Double32_t     fLength;            //!  length
    Double32_t     fELoss;             //!  energy loss
    
    /** container for data points */
    TClonesArray*  fHptPointCollection;
    
    Int_t InitMedium(const char* name);
    
    
    
protected:
    
    Double_t DimX;
    Double_t DimY;
    Double_t DimZ;
    Double_t zSizeMudet; //dimension of the Muon Detector volume
    Double_t fConcreteX; //dimesion of Concrete Base on which the external HPTs lie
    Double_t fConcreteY;
    Double_t fConcreteZ;

    Double_t fSRHeight;
    Double_t fDesign;
    Double_t fDistance;
    Int_t fnHPT;

    Double_t fmagnety; //parameters from EmuMagnet
    Double_t fmagnetcenter;

    Int_t fntarget;

    Hpt(const Hpt&);
    Hpt& operator=(const Hpt&);
    ClassDef(Hpt,5)

};
#endif 

