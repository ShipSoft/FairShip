#ifndef SCINTILLATOR_H
#define SCINTILLATOR_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"                  // for FairDetector

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class ScintillatorPoint;
class FairVolume;
class TClonesArray;

class Scintillator:public FairDetector
{
  public:
  Scintillator(const char* name, Bool_t Active, const char* Title="Scintillator");
    Scintillator();
    virtual ~Scintillator();
      
    void ConstructGeometry();

    void SetScoring1XY(Float_t Scoring1X, Float_t Scoring1Y);
    
    void SetDistT1(Float_t DistT1);
    void SetDistT2(Float_t DistT2);
    void SetS_T1coords(Float_t S_T1_x, Float_t S_T1_y);   
    void SetS_T2coords(Float_t S_T2_x, Float_t S_T2_y);     
    
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
    ScintillatorPoint* AddHit(Int_t trackID, Int_t detID,
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
             
    Float_t     fScoring1X;            //width of 1st scintillator
    Float_t     fScoring1Y;            //height of 1st scintillator
    Float_t     fDistT1;            //distance from scintillator to center of first tube   
    Float_t     fDistT2;            //distance from scintillator 2 to center of last tube   
    Float_t     fS_T1_x;            //
    Float_t     fS_T1_y;            //  
    Float_t     fS_T2_x;            //
    Float_t     fS_T2_y;            //      
       
    /** container for data points */
    TClonesArray*  fScintillatorPointCollection;
    
    Int_t InitMedium(const char* name);
        
    Scintillator(const Scintillator&);
    Scintillator& operator=(const Scintillator&);
    ClassDef(Scintillator,1)

};
#endif 
