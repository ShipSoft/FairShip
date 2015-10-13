#ifndef VETO_H
#define VETO_H

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"

class vetoPoint;
class FairVolume;
class TClonesArray;

class veto: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    veto(const char* Name, Bool_t Active);

    /**      default constructor    */
    veto();

    /**       destructor     */
    virtual ~veto();

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

    void SetFastMuon() {fFastMuon=true;}  // kill all tracks except of muons

    /**      Create the detector geometry        */
    void ConstructGeometry();

    void SetZpositions(Float_t z0, Float_t z1, Float_t z2, Float_t z3, Float_t z4, Int_t c);
    void SetTubZpositions(Float_t z1, Float_t z2, Float_t z3, Float_t z4, Float_t z5, Float_t z6);
    void SetTublengths(Float_t l1, Float_t l2, Float_t l3, Float_t l4, Float_t l5, Float_t l6);
    void SetB(Float_t b) {fBtube=b;}
    void SetRminRmax(Float_t rmin,Float_t rmax){
     fRmin = rmin;                                                //!  minimum diameter of vacuum chamber
     fRmax = rmax;                                                //!  maximum diameter of vacuum chamber
     }
    void SetVminVmax(Float_t rmin,Float_t rmax)
    {
     fVRmin = rmin;                                                //!  minimum diameter liquid scintillator layer
     fVRmax = rmax;                                                //!  maximum diameter liquid scintillator layer
    }
    /**      This method is an example of how to add your own point
     *       of type vetoPoint to the clones array
    */
    vetoPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom);

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


  private:

    /** Track information to be stored until the track leaves the
    active volume.
    */
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Float_t     fTime;              //!  time
    Float_t     fLength;            //!  length
    Float_t     fELoss;             //!  energy loss
    Float_t     fT0z;               //!  z-position of veto station
    Float_t     fT1z;               //!  z-position of tracking station 1
    Float_t     fT2z;               //!  z-position of tracking station 2
    Float_t     fT3z;               //!  z-position of tracking station 3
    Float_t     fT4z;               //!  z-position of tracking station 4
    Int_t          fDesign;            //!  1: cylindrical with basic tracking chambers, 
                                       //   2: conical with basic tracking chambers, but no trscking chamber at entrance 
                                       //   3: cylindrical, no tracking chambers defined but sensitive walls, strawchambers separated
    Bool_t     fFastMuon;
    Float_t fTub1z;
    Float_t fTub2z;
    Float_t fTub3z;
    Float_t fTub4z;
    Float_t fTub5z;
    Float_t fTub6z;
    Float_t fTub1length;
    Float_t fTub2length;
    Float_t fTub3length;
    Float_t fTub4length;
    Float_t fTub5length;
    Float_t fTub6length;
    Float_t fRmin;
    Float_t fRmax;
    Float_t fVRmin;
    Float_t fVRmax;
    Float_t fBtube;
    /** container for data points */

    TClonesArray*  fvetoPointCollection;

    veto(const veto&);
    veto& operator=(const veto&);
    Int_t InitMedium(const char* name);
    TGeoVolume* GeoEllipticalTube(const char* name,Double_t thick,Double_t a,Double_t b,Double_t dz,Int_t colour,TGeoMedium *material,Bool_t sense);
    void GeoPlateEllipse(const char* name,Double_t thick,Double_t a,Double_t b,Double_t dz,Double_t z,Int_t colour,TGeoMedium *material,TGeoVolume *top);
    ClassDef(veto,2)
};

#endif //VETO_H
