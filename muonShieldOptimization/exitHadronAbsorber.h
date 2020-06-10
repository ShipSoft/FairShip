#ifndef EXITHADRONABSORBER_H
#define EXITHADRONABSORBER_H

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "TGeoVolume.h"
#include "vetoPoint.h"
#include "TNtuple.h"
#include <map>

class FairVolume;
class TClonesArray;

class exitHadronAbsorber: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    exitHadronAbsorber(const char* Name, Bool_t Active);

    /**      default constructor    */
    exitHadronAbsorber();

    /**       destructor     */
    virtual ~exitHadronAbsorber();

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
    virtual void   PostTrack() {;}
    virtual void   PreTrack();
    virtual void   BeginEvent() {;}

    vetoPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom);
    inline void SetEnergyCut(Float_t emax) {EMax=emax;}// min energy to be copied to Geant4
    inline void SetOnlyMuons(){fOnlyMuons=kTRUE;}
    inline void SetOpt4DP(){withNtuple=kTRUE;}
    inline void SkipNeutrinos(){fSkipNeutrinos=kTRUE;}
    inline void SetZposition(Float_t x){fzPos=x;}

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
    Double_t     fzPos;              //!  zPos, optional
    Bool_t withNtuple;               //! special option for Dark Photon physics studies
    TNtuple* fNtuple;               //!  
    Float_t EMax;  //! max energy to transport
    Bool_t fOnlyMuons;  //! flag if only muons should be stored
    Bool_t fSkipNeutrinos;  //! flag if neutrinos should be ignored
    TFile* fout; //!
    TClonesArray* fElectrons; //!
    Int_t index;
    /** container for data points */
    TClonesArray*  fexitHadronAbsorberPointCollection;
    ClassDef(exitHadronAbsorber, 0)
};

#endif //EXITHADRONABSORBER_H
