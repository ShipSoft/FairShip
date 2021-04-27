#ifndef boxTarget_H
#define boxTarget_H

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "TGeoVolume.h"
#include "vetoPoint.h"
#include "TString.h"
#include <map>

class FairVolume;
class TClonesArray;

class boxTarget: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    boxTarget(const char* Name, Bool_t Active);

    /**      default constructor    */
    boxTarget();

    /**       destructor     */
    virtual ~boxTarget();

    /**      Initialization of the detector is done here    */
    virtual void   Initialize();

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

    /**      Create the detector geometry        */
    void ConstructGeometry();

    /** The following methods can be implemented if you need to make
     *  any optional action in your detector during the transport.
    */

    virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 ,
                               Int_t offset) {;}
    virtual void   SetSpecialPhysicsCuts() {;}
    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun();
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack(){;}
    virtual void   PreTrack(){;}
    virtual void   BeginEvent() {;}

    vetoPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom);
    inline void SetTarget(TString material, Float_t L,Bool_t choice ){fTargetMaterial = material; fTargetL=L; fBox=choice;}
  private:
    Int_t InitMedium(TString name);
    /** Track information to be stored until the track leaves the
    active volume.
    */
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double_t     fTime;              //!  time
    Double_t    fLength;              //!  track length
    TString  fTargetMaterial;        //! target material
    Float_t  fTargetL;                 //! target length
    Int_t index;
    Bool_t fBox;
    /** container for data points */
    TClonesArray*  fboxTargetPointCollection;
    ClassDef(boxTarget, 1)
};

#endif //boxTarget_H
