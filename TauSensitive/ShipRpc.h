#ifndef Rpc_H
#define Rpc_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class ShipRpcPoint;
class FairVolume;
class TClonesArray;

class ShipRpc : public FairModule
{
  public:
    ShipRpc(const char* name, const Double_t zRpcL, const Double_t zDriftL, const Double_t DriftL, const Double_t IronL, const Double_t ScintL, const Double_t MiddleG, Bool_t Active, const char* Title = "Rpc");
    ShipRpc();
    virtual ~ShipRpc();
    void ConstructGeometry();
    
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
    ShipRpcPoint* AddHit(Int_t trackID, Int_t detID,
                      TVector3 pos, TVector3 mom,
                      Double_t time, Double_t length,
                      Double_t eLoss);
    
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

    
    ShipRpc(const ShipRpc&);
    ShipRpc& operator=(const ShipRpc&);
    
    ClassDef(ShipRpc,1)
    
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
    TClonesArray*  fShipRpcPointCollection;
    
protected:
  
    
    Double_t     zRpcLayer;
    Double_t     zDriftLayer;
    Double_t     DriftLenght;    //dimension along z axis of Drift tubes
    Double_t     IronLenght;      //dimension along z axis of iron layer in spectrometer
    Double_t     ScintLenght;   //dimension along z axis of scintillator layer
    Double_t     MiddleGap;     //distance between the last plane of the 1st spectro and the 1st plane of the 2nd spectro
  Int_t InitMedium(const char* name);

};

#endif //MuonShield_H

