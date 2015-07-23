#ifndef MAGNETICSPECTROMETER_H
#define MAGNETICSPECTROMETER_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"                  // for FairDetector

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class ShipRpcPoint;
class FairVolume;
class TClonesArray;

class MagneticSpectrometer:public FairDetector
{
  public:
    MagneticSpectrometer(const char* name, const Double_t zMSC, const Double_t zSize, const Double_t FeSlab, const Double_t RpcW, const Double_t ArmW, const Double_t GapV, const Double_t MGap, const Double_t Mfield, Double_t HPTW, Double_t RetYokeH, Bool_t Active, const char* Title="MagneticSpectrometer");
    MagneticSpectrometer();
    virtual ~MagneticSpectrometer();
    
    void SetCoilParameters(Double_t CoilH, Double_t CoilW, Int_t N, Double_t CoilG);
    
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
    /*ShipRpcPoint* AddHit(Int_t trackID, Int_t detID,
                         TVector3 pos, TVector3 mom,
                         Double_t time, Double_t length,
                         Double_t eLoss, Int_t pdgCode,Int_t nArm, Int_t nRpc, Int_t nHpt);
    */

    ShipRpcPoint* AddHit(Int_t trackID, Int_t detID,
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

    void DecodeVolumeID(Int_t detID,int &nHPT,int &nARM,int &nRPC);
    
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
    TClonesArray*  fShipRpcPointCollection;
    
    Int_t InitMedium(const char* name);
    
    
    
protected:
    
    Double_t zMSCenter; //z distance of the center of the spectrometer in cm from the center of the vacuum tube
    Double_t zSizeMS; //Dimension of the whole magnetic spectrometr (1st + 2nd arm + HPTs) alogn beam axis
    Double_t IronSlabWidth; // Width of the Iron Slabs
    Double_t RpcWidth; // Width of the Rpc planes
    Double_t HPTWidth; // Width of the HPT planes
    Double_t ArmWidth; // Width of the Spectrometer Arms
    Double_t GapFromVessel; //distance between the end of the second arm of the spectrometer and the decay vessel
    Double_t MiddleGap; // distance between the two arms of the spectrometer
    Double_t MagneticField;
    Double_t ReturnYokeH;
    
    Double_t CoilGap;
    Double_t CoilHeight;
    Double_t CoilWidth;
    Int_t NCoils;
    
    
    MagneticSpectrometer(const MagneticSpectrometer&);
    MagneticSpectrometer& operator=(const MagneticSpectrometer&);
    ClassDef(MagneticSpectrometer,1)

};



#endif //TAUMAGNETICSPECTROMETER_H

