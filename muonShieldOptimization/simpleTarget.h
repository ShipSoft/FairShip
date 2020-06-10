#ifndef simpleTarget_H
#define simpleTarget_H

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "TGeoVolume.h"
#include "vetoPoint.h"
#include <map>

class FairVolume;
class TClonesArray;

class simpleTarget: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    simpleTarget(const char* Name, Bool_t Active);

    /**      default constructor    */
    simpleTarget();

    /**       destructor     */
    virtual ~simpleTarget();

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
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack();
    virtual void   BeginEvent() {;}

    vetoPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom);
    inline void SetEnergyCut(Float_t emax) {EMax=emax;}// min energy to be copied to Geant4
    inline void SetOnlyMuons(){fOnlyMuons=kTRUE;}
    inline void SetFastMuon(){fFastMuon=kTRUE;}
    inline void SetParameters(TString m,Float_t l,Float_t z){fMaterial=m;fThick=l;fzPos=z;}

  private:

    /** Track information to be stored until the track leaves the
    active volume.
    */
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double_t     fTime;              //!  time
    Double_t     fLength;            //!  length
    Double_t     fzPos;              //!  zPos
    Double_t     fThick;             //!  thickness
    Double_t     fELoss;              //!  
    Double_t     fTotalEloss;         //!  
    TString      fMaterial;           //!  material
    Float_t EMax;  //! max energy to transport
    Bool_t fOnlyMuons;  //!
    Bool_t fFastMuon;  //! for fast processing
    TFile* fout;
    /** container for data points */
    TClonesArray*  fsimpleTargetPointCollection;
    ClassDef(simpleTarget, 0)
};

#endif //simpleTarget_H
