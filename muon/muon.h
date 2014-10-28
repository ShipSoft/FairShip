#ifndef VETO_H
#define VETO_H

#include "FairDetector.h"

#include "TVector3.h"
#include "TLorentzVector.h"

class muonPoint;
class FairVolume;
class TClonesArray;

class muon: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    muon(const char* Name, Bool_t Active);

    /**      default constructor    */
    muon();

    /**       destructor     */
    virtual ~muon();

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

    void SetZStationPositions(Double32_t z0, Double32_t z1,Double32_t z2,Double32_t z3);

    void SetZFilterPositions(Double32_t z0, Double32_t z1,Double32_t z2);

    void SetActiveThickness(Double32_t activeThickness);

    void SetFilterThickness(Double32_t filterThickness);

    void SetXMax(Double32_t xMax);

    void SetYMax(Double32_t yMax);


    /**      Create the detector geometry        */
    void ConstructGeometry();



    /**      This method is an example of how to add your own point
     *       of type muonPoint to the clones array
    */
    muonPoint* AddHit(Int_t trackID, Int_t detID,
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
    Double32_t     fM0z;               //!  z-position of veto station
    Double32_t     fM1z;               //!  z-position of tracking station 1
    Double32_t     fM2z;               //!  z-position of tracking station 2
    Double32_t     fM3z;               //!  z-position of tracking station 3
    Double32_t     fF0z;               //!  z-position of veto station
    Double32_t     fF1z;               //!  z-position of tracking station 1
    Double32_t     fF2z;               //!  z-position of tracking station 2
 
    Double32_t fFilterThickness;
    Double32_t fActiveThickness;
    Double32_t fXMax;
    Double32_t fYMax;
    /** container for data points */

    TClonesArray*  fmuonPointCollection;

    muon(const muon&);
    muon& operator=(const muon&);
    Int_t InitMedium(const char* name);

    ClassDef(muon,1)
};

#endif //VETO_H
