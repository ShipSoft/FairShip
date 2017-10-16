#ifndef MUFLUXSPECTROMETER_H
#define MUFLUXSPECTROMETER_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"                  // for FairDetector

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class MufluxSpectrometerPoint;
class FairVolume;
class TClonesArray;

class MufluxSpectrometer:public FairDetector
{
  public:
   MufluxSpectrometer(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ,Bool_t Active, const char* Title="Magnetic  MufluxSpectrometer");
    MufluxSpectrometer();
    virtual ~MufluxSpectrometer();
      
    void ConstructGeometry();
    void SetZsize(const Double_t MSsize);
    void SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox);
    
    //methods for drift tubes by Eric
    void SetTubeLength(Double_t tubelength);
    void SetInnerTubeDiameter(Double_t innertubediameter);
    void SetOuterTubeDiameter(Double_t outertubediameter);
    void SetTubePitch(Double_t tubepitch);
    void SetDeltazLayer(Double_t deltazlayer);
    void SetDeltazPlane(Double_t deltazplane);
    void SetTubesPerLayer(Int_t tubesperlayer);
    void SetStereoAngle(Int_t stereoangle);
    void SetWireThickness(Double_t wirethickness);
    void SetDeltazView(Double_t deltazview);
    void SetTubeLength12(Double_t strawlength12);
    void SetVacBox_x(Double_t vacbox_x);
    void SetVacBox_y(Double_t vacbox_y);
    void SetTr12YDim(Double_t tr12ydim); 
    void SetTr34YDim(Double_t tr34ydim); 
    void SetTr12XDim(Double_t tr12xdim); 
    void SetTr34XDim(Double_t tr34xdim);   
    void SetMuonFlux(Bool_t muonflux);   
    void TubeDecode(Int_t detID,int &statnb,int &vnb,int &pnb,int &lnb, int &snb);
    void TubeEndPoints(Int_t detID, TVector3 &top, TVector3 &bot);

// for the digitizing step
    void SetTubeResolution(Double_t a, Double_t b) {v_drift = a; sigma_spatial=b;}
    Double_t TubeVdrift() {return v_drift;}
    Double_t TubeSigmaSpatial() {return sigma_spatial;}    
    
     //methods for Goliath by Annarita
    void SetGoliathSizes(Double_t H, Double_t TS, Double_t LS, Double_t BasisH);
    void SetCoilParameters(Double_t CoilR, Double_t UpCoilH, Double_t LowCoilH, Double_t CoilD);
    //
    /**      Initialization of the detector is done here    */
    virtual void Initialize();
    
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
    
    /**      This method is an example of how to add your own point
     *       of type muonPoint to the clones array
     *       dsit2Wire is used by the drifttubes
     */    
    MufluxSpectrometerPoint* AddHit(Int_t trackID, Int_t detID,
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

    void DecodeVolumeID(Int_t detID,int &nHPT);
    
private:
    
    /** Track information to be stored until the track leaves the
     active volume.
     */
    Int_t          fTrackID;                 //!  track index
    Int_t          fPdgCode;                 //!  pdg code
    Int_t          fVolumeID;                //!  volume id
    TLorentzVector fPos;                     //!  position at entrance
    TLorentzVector fMom;                     //!  momentum at entrance
    Double32_t     fTime;                    //!  time
    Double32_t     fLength;                  //!  length
    
    Double32_t     fELoss;                   //!  energy loss
    Double_t       fTube_length;             //!  Length (y) of a tube
    Double_t       fTube_length_12;          //!  tubelength for tracking station 1 & 2
    Double_t       fInner_Tube_diameter;     //!  Inner Tube diameter
    Double_t       fOuter_Tube_diameter;     //!  Outer Straw diameter
    Double_t       fTubes_pitch;             //!  Distance (x) between tubes in one layer
    Double_t       fDeltaz_layer12;          //!  Distance (z) between layer 1&2
    Double_t       fDeltaz_plane12;          //!  Distance (z) between plane 1&2
    Double_t       fOffset_layer12;          //!  Offset (x) between straws of layer2&1
    Double_t       fOffset_plane12;          //!  Offset (x) between straws of plane1&2
    Int_t          fTubes_per_layer;         //!  Number of tubes in one layer
    Double_t       fView_angle;              //!  Stereo angle of layers in a view
    Double_t       fcosphi;
    Double_t       fsinphi;
    Double_t       fWire_thickness;          //!  Thickness of the wire
    Double_t       fDeltaz_view;             //!  Distance (z) between views
    Double_t       fVacBox_x;              //!  x size of station vacuumbox
    Double_t       fVacBox_y;                //!  y size of station vacuumbox
    Double_t       fvetoydim;                //!  y size of veto station
    Double_t       ftr12ydim;                //!  y size of tr12 stations
    Double_t       ftr34ydim;                //!  y size of tr34 stations
    Double_t       ftr12xdim;                //!  x size of tr12 stations
    Double_t       ftr34xdim;                //!  x size of tr34 stations
    Int_t          fTubes_per_layer_tr12;    //!  Number of tubes in one tr12 layer
    Int_t          fTubes_per_layer_tr34;    //!  Number of tubes in one tr34 layer
    Double_t       v_drift;                  //! drift velocity  
    Double_t       sigma_spatial;            //! spatial resolution    
    Bool_t         fMuonFlux;                //! set up for muonflux    
    
    /** container for data points */
    TClonesArray*  fMufluxSpectrometerPointCollection;
    
    Int_t InitMedium(const char* name);
        
protected:

    //Goliath by Annarita
    
    Double_t Height;
    // Double_t zCenter;
    Double_t LongitudinalSize;
    Double_t TransversalSize;
    //Double_t GapFromTSpectro;
    Double_t CoilRadius;
    Double_t UpCoilHeight;
    Double_t LowCoilHeight;
    Double_t CoilDistance;
    Double_t BasisHeight;
    //
    
    Double_t SBoxX = 0;
    Double_t SBoxY = 0;
    Double_t SBoxZ = 0;

    Double_t BoxX = 0;
    Double_t BoxY = 0;
    Double_t BoxZ = 0;
    Double_t zBoxPosition = 0;
    
    Double_t DimX =0;
    Double_t DimY =0;
    Double_t DimZ = 0;
    Double_t zSizeMS = 0; //dimension of the Magnetic Spectrometer volume
    
    MufluxSpectrometer(const MufluxSpectrometer&);
    MufluxSpectrometer& operator=(const MufluxSpectrometer&);
    ClassDef(MufluxSpectrometer,1)

};
#endif 
