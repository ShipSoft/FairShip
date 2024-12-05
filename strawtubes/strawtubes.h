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

    strawtubes(std::string medium);

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

    void SetZpositions(Double_t z0, Double_t z1, Double_t z2, Double_t z3, Double_t z4);
    void SetStrawLength(Double_t strawlength);
    void SetInnerStrawDiameter(Double_t innerstrawdiameter);
    void SetOuterStrawDiameter(Double_t outerstrawdiameter);
    void SetStrawPitch(Double_t strawpitch,Double_t layer_offset, Double_t plane_offset);
    void SetDeltazLayer(Double_t deltazlayer);
    void SetDeltazPlane(Double_t deltazplane);
    void SetStrawsPerLayer(Int_t strawsperlayer);
    void SetStereoAngle(Double_t stereoangle);
    void SetWireThickness(Double_t wirethickness);
    void SetDeltazFrame(Double_t deltazframe);
    void SetFrameLateralWidth(Double_t framelateralwidth);
    void SetFrameMaterial(TString framematerial);
    void SetDeltazView(Double_t deltazview);
    void SetStrawLength12(Double_t strawlength12);
    void SetStrawLengthVeto(Double_t strawlengthveto);
    void SetVacBox_x(Double_t vacbox_x);
    void SetVacBox_y(Double_t vacbox_y);
    void SetVetoYDim(Double_t vetoydim);
    void SetTr12YDim(Double_t tr12ydim);
    void SetTr34YDim(Double_t tr34ydim);
    void StrawDecode(Int_t detID,int &statnb,int &vnb,int &pnb,int &lnb, int &snb);
    void StrawEndPoints(Int_t detID, TVector3 &top, TVector3 &bot);
    void StrawEndPointsOriginal(Int_t detID, TVector3 &top, TVector3 &bot);
// for the digitizing step
    void SetStrawResolution(Double_t a, Double_t b) {v_drift = a; sigma_spatial=b;}
    Double_t StrawVdrift() {return v_drift;}
    Double_t StrawSigmaSpatial() {return sigma_spatial;}

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
    Double_t     fTime;                   //!  time
    Double_t     fLength;                 //!  length
    Double_t     fELoss;                  //!  energy loss
    Double_t     fT0z;                    //!  z-position of veto station
    Double_t     fT1z;                    //!  z-position of tracking station 1
    Double_t     fT2z;                    //!  z-position of tracking station 2
    Double_t     fT3z;                    //!  z-position of tracking station 3
    Double_t     fT4z;                    //!  z-position of tracking station 4
    Double_t     fStraw_length;           //!  Length (y) of a straw
    Double_t     fStraw_length_12;        //!  strawlength for tracking station 1 & 2
    Double_t     fStraw_length_veto;      //!  strawlength for veto station
    Double_t     fInner_Straw_diameter;   //!  Inner Straw diameter
    Double_t     fOuter_Straw_diameter;   //!  Outer Straw diameter
    Double_t     fStraw_pitch;            //!  Distance (x) between straws in one layer
    Double_t     fDeltaz_layer12;         //!  Distance (z) between layer 1&2
    Double_t     fDeltaz_plane12;         //!  Distance (z) between plane 1&2
    Double_t     fOffset_layer12;         //!  Offset (x) between straws of layer2&1
    Double_t     fOffset_plane12;         //!  Offset (x) between straws of plane1&2
    Int_t        fStraws_per_layer;       //!  Number of straws in one layer
    Double_t     fView_angle;             //!  Stereo angle of layers in a view
    Double_t     fcosphi;
    Double_t     fsinphi;
    Double_t     fWire_thickness;         //!  Thickness of the wire
    Double_t     fDeltaz_frame;           //!  Thickness (z) of the meterial frame
    Double_t     fFrame_lateral_width;    //!  Width (x and y) of the material frame
    TString      fFrame_material;         //!  Material of the view frame
    Double_t     fDeltaz_view;            //!  Distance (z) between views
    Double_t     fVacBox_x;               //!  x size of station vacuumbox
    Double_t     fVacBox_y;               //!  y size of station vacuumbox
    Double_t     fvetoydim;               //!  y size of veto station
    Double_t     ftr12ydim;               //!  y size of tr12 stations
    Double_t     ftr34ydim;               //!  y size of tr34 stations
    Int_t        fStraws_per_layer_veto;  //!  Number of straws in one veto layer
    Int_t        fStraws_per_layer_tr12;  //!  Number of straws in one tr12 layer
    Int_t        fStraws_per_layer_tr34;  //!  Number of straws in one tr34 layer
    Double_t     v_drift;                 //! drift velocity
    Double_t     sigma_spatial;           //! spatial resolution
    std::string fMedium;                  //! vacuum box medium
    /** container for data points */

    TClonesArray* fstrawtubesPointCollection;

    strawtubes(const strawtubes&);
    strawtubes& operator=(const strawtubes&);
    Int_t InitMedium(const char* name);
    ClassDef(strawtubes,5)
};

#endif //STRAWTUBES_H
