#ifndef PRESHOWER_H
#define PRESHOWER_H

#include "FairDetector.h"

#include "TVector3.h"
#include "TLorentzVector.h"

class preshowerPoint;
class FairVolume;
class TClonesArray;

class preshower: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    preshower(const char* Name, Bool_t Active);

    /**      default constructor    */
    preshower();

    /**       destructor     */
    virtual ~preshower();

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

    void SetZStationPosition2(Double_t z0,Double_t z1);

    void SetZFilterPosition2(Double_t z0,Double_t z1);

    void SetActiveThickness(Double_t activeThickness );

    void SetFilterThickness2(Double_t filterThickness0,Double_t filterThickness1);

    void SetXMax(Double_t xMax);

    void SetYMax(Double_t yMax);


    /**      Create the detector geometry        */
    void ConstructGeometry();



    /**      This method is an example of how to add your own point
     *       of type preshowerPoint to the clones array
    */
    preshowerPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode);

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
    Double_t     fTime;              //!  time
    Double_t     fLength;            //!  length
    Double_t     fELoss;             //!  energy loss
    Double_t     fM0z;               //!  z-position of veto station
    Double_t     fM1z;               //!  z-position of tracking station 1
    // Double_t     fM2z;               //!  z-position of tracking station 2
    // Double_t     fM3z;               //!  z-position of tracking station 3
    Double_t     fF0z;               //!  z-position of veto station
    Double_t     fF1z;               //!  z-position of tracking station 1
    // Double_t     fF2z;               //!  z-position of tracking station 2
 
    Double_t fFilterThickness0;
    Double_t fActiveThickness;
    Double_t fFilterThickness1;
    // Double_t fActiveThickness1;
    Double_t fXMax;
    Double_t fYMax;
    /** container for data points */

    TClonesArray*  fpreshowerPointCollection;

    preshower(const preshower&);
    preshower& operator=(const preshower&);
    Int_t InitMedium(const char* name);

    ClassDef(preshower,1)
};

#endif //PRESHOWER_H
