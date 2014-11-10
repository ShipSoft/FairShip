#ifndef STRAWTUBES_H
#define STRAWTUBES_H

#include "FairDetector.h"

#include "TVector3.h"
#include "TLorentzVector.h"

class strawtubesPoint;
class FairVolume;
class TClonesArray;

class strawtubes: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    strawtubes(const char* Name, Bool_t Active);

    /**      default constructor    */
    strawtubes();

    /**       destructor     */
    virtual ~strawtubes();

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

    void SetZpositions(Double32_t z0, Double32_t z1, Double32_t z2, Double32_t z3, Double32_t z4);
    void SetStrawLength(Double32_t strawlength);
    void SetInnerStrawDiameter(Double32_t innerstrawdiameter);
    void SetOuterStrawDiameter(Double32_t outerstrawdiameter);
    void SetStrawPitch(Double32_t strawpitch);
    void SetDeltazLayer(Double32_t deltazlayer);
    void SetDeltazPlane(Double32_t deltazplane);
    void SetStrawsPerLayer(Int_t strawsperlayer);
    void SetStereoAngle(Int_t stereoangle);
    void SetWireThickness(Double32_t wirethickness);
    void SetDeltazView(Double32_t deltazview);
    void SetVacBox_x(Double32_t vacbox_x);
    void SetVacBox_y(Double32_t vacbox_y);
    void StrawDecode(Int_t detID,int &statnb,int &vnb,int &pnb,int &lnb, int &snb);
    void StrawEndPoints(Int_t detID, TVector3 &top, TVector3 &bot);

    /**      Create the detector geometry        */
    void ConstructGeometry();



    /**      This method is an example of how to add your own point
     *       of type strawtubesPoint to the clones array
    */
    strawtubesPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss, Int_t pdgCode, Double_t dist2Wire);

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
    Int_t          fTrackID;                //!  track index
    Int_t          fVolumeID;               //!  volume id
    TLorentzVector fPos;                    //!  position at entrance
    TLorentzVector fMom;                    //!  momentum at entrance
    Double32_t     fTime;                   //!  time
    Double32_t     fLength;                 //!  length
    Double32_t     fELoss;                  //!  energy loss
    Double32_t     fT0z;                    //!  z-position of veto station
    Double32_t     fT1z;                    //!  z-position of tracking station 1
    Double32_t     fT2z;                    //!  z-position of tracking station 2
    Double32_t     fT3z;                    //!  z-position of tracking station 3
    Double32_t     fT4z;                    //!  z-position of tracking station 4
    Double32_t     fStraw_length;           //!  Length (y) of a straw
    Double32_t     fInner_Straw_diameter;   //!  Inner Straw diameter
    Double32_t     fOuter_Straw_diameter;   //!  Outer Straw diameter
    Double32_t     fStraw_pitch;            //!  Distance (x) between straws in one layer
    Double32_t     fDeltaz_layer12;         //!  Distance (z) between layer 1&2
    Double32_t     fDeltaz_plane12;         //!  Distance (z) between plane 1&2
    Double32_t     fOffset_layer12;         //!  Offset (x) between straws of layer2&1
    Double32_t     fOffset_plane12;         //!  Offset (x) between straws of plane1&2
    Int_t          fStraws_per_layer;       //!  Number of straws in one layer
    Double32_t     fView_angle;             //!  Stereo angle of layers in a view
    Double32_t     fcosphi;
    Double32_t     fsinphi;
    Double32_t     fWire_thickness;         //!  Thickness of the wire
    Double32_t     fDeltaz_view;            //!  Distance (z) between views
    Double32_t     fVacBox_x;               //!  x size of station vacuumbox
    Double32_t     fVacBox_y;               //!  y size of station vacuumbox
    /** container for data points */

    TClonesArray*  fstrawtubesPointCollection;

    strawtubes(const strawtubes&);
    strawtubes& operator=(const strawtubes&);
    Int_t InitMedium(const char* name);
    ClassDef(strawtubes,1)
};

#endif //STRAWTUBES_H
