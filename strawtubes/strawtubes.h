// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef STRAWTUBES_STRAWTUBES_H_
#define STRAWTUBES_STRAWTUBES_H_

#include "FairDetector.h"

#include "TVector3.h"
#include "TLorentzVector.h"

class strawtubesPoint;
class FairVolume;
class TClonesArray;
class tuple;

class strawtubes: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
        strawtubes(const char* Name, Bool_t Active);

    explicit strawtubes(std::string medium);

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

    void SetzPositions(Double_t z1, Double_t z2, Double_t z3, Double_t z4);
    void SetApertureArea(Double_t width, Double_t height);
    void SetStrawDiameter(Double_t outer_straw_diameter, Double_t wall_thickness);
    void SetStrawPitch(Double_t straw_pitch, Double_t layer_offset);
    void SetDeltazLayer(Double_t delta_z_layer);
    void SetStereoAngle(Double_t stereo_angle);
    void SetWireThickness(Double_t wire_thickness);
    void SetFrameMaterial(TString frame_material);
    void SetDeltazView(Double_t delta_z_view);
    void SetStationEnvelope(Double_t x, Double_t y, Double_t z);
    static std::tuple<Int_t, Int_t, Int_t, Int_t> StrawDecode(Int_t detID);
    static void StrawEndPoints(Int_t detID, TVector3& top, TVector3& bot);
// for the digitizing step
    void SetStrawResolution(Double_t a, Double_t b)
    {
        v_drift = a;
        sigma_spatial = b;
    }
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
    Int_t fTrackID;                         //!  track index
    Int_t fVolumeID;                        //!  volume id
    TLorentzVector fPos;                    //!  position at entrance
    TLorentzVector fMom;                    //!  momentum at entrance
    Double_t fTime;                         //!  time
    Double_t fLength;                       //!  length
    Double_t fELoss;                        //!  energy loss
    Double_t f_T1_z;                        //!  z-position of tracking station 1
    Double_t f_T2_z;                        //!  z-position of tracking station 2
    Double_t f_T3_z;                        //!  z-position of tracking station 3
    Double_t f_T4_z;                        //!  z-position of tracking station 4
    Double_t f_aperture_width;              //!  Aperture width (x)
    Double_t f_aperture_height;             //!  Aperture height (y)
    Double_t f_inner_straw_diameter;        //!  Inner Straw diameter
    Double_t f_outer_straw_diameter;        //!  Outer Straw diameter
    Double_t f_straw_pitch;                 //!  Distance (y) between straws in a layer
    Double_t f_offset_layer;                //!  Offset (y) of straws between layers
    Double_t f_delta_z_layer;               //!  Distance (z) between layers
    Double_t f_view_angle;                  //!  Stereo view angle
    Double_t f_wire_thickness;              //!  Sense wire thickness
    TString  f_frame_material;              //!  Structure frame material
    Double_t f_delta_z_view;                //!  Distance (z) between stereo views
    Double_t f_station_width;               //!  Station envelope width (x)
    Double_t f_station_height;              //!  Station envelope height (y)
    Double_t f_station_length;              //!  Station envelope length (z)
    Double_t v_drift;                       //! drift velocity
    Double_t sigma_spatial;                 //! spatial resolution
    std::string fMedium;                    //! vacuum box medium
    /** container for data points */

    TClonesArray* fstrawtubesPointCollection;

    strawtubes(const strawtubes&);
    strawtubes& operator=(const strawtubes&);
    Int_t InitMedium(const char* name);
    ClassDef(strawtubes, 6)
};

#endif  // STRAWTUBES_STRAWTUBES_H_
