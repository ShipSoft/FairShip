#ifndef MUONTAGGER_H
#define MUONTAGGER_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class MuonTaggerPoint;
class FairVolume;
class TClonesArray;

class MuonTagger : public FairDetector
{
public:
  MuonTagger(const char* name, const Double_t BX, const Double_t BY, const Double_t BZ, const Double_t zBox, Bool_t Active, const char* Title = "MuonTagger");
    MuonTagger();
    virtual ~MuonTagger();
    
    /**      Create the detector geometry        */
    void ConstructGeometry();

    void SetPassiveParameters(Double_t PX, Double_t PY, Double_t PTh);
    void SetSensitiveParameters(Double_t SX, Double_t SY, Double_t STh);
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
    
    /**      How to add your own point of type MuonPoint to the clones array */

    MuonTaggerPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
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
    
       
    MuonTagger(const MuonTagger&);
    MuonTagger& operator=(const MuonTagger&);
    
    ClassDef(MuonTagger,1)
    
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
    TClonesArray*  fMuonTaggerPointCollection;
    
protected:
    
    Double_t   BoxX;
    Double_t   BoxY;
    Double_t   BoxZ;
    Double_t zBoxPosition;
    
    Int_t InitMedium(const char* name);

    //exclusive for the muon filter
    Double_t PasX;
    Double_t PasY;
    Double_t PasThickness;
    
    Double_t SensX;
    Double_t SensY;
    Double_t SensThickness;
};

#endif

