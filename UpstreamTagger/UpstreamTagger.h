#ifndef UPSTREAMTAGGER_UPSTREAMTAGGER_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGER_H_

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "ShipUnit.h"

class UpstreamTaggerPoint;
class FairVolume;
class TClonesArray;

using ShipUnit::m;
using ShipUnit::cm;

/**
 * @brief Upstream Background Tagger (UBT) detector
 *
 * The UBT is a simplified scoring plane detector implemented as a vacuum box.
 * It serves as a background tagging device upstream of the decay volume.
 *
 * Historical Note:
 * The UBT was previously implemented as a detailed RPC (Resistive Plate Chamber)
 * with multiple material layers (Glass, PMMA, Freon SF6, FR4, Aluminium, strips).
 * It was simplified to a single vacuum box scoring plane to avoid geometry overlaps
 * and reduce simulation complexity while maintaining its physics purpose.
 * See commits 178787588 and related for the simplification history.
 *
 * Current Implementation:
 * - Simple vacuum box with configurable dimensions
 * - Default dimensions: 4.4m (X) × 6.4m (Y) × 16cm (Z)
 * - Z position and box dimensions are set from geometry_config.py
 * - Configured via SetZposition() and SetBoxDimensions()
 */

class UpstreamTagger: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    UpstreamTagger(const char* Name, Bool_t Active);

    /** default constructor */
    UpstreamTagger();

    /** destructor */
    virtual ~UpstreamTagger();

    /** Initialization of the detector is done here */
    virtual void   Initialize();

    /**   this method is called for each step during simulation
     *    (see FairMCApplication::Stepping())
    */
    virtual Bool_t ProcessHits( FairVolume* v=0);

    /**       Registers the produced collections in FAIRRootManager. */
    virtual void Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const;

    /** has to be called after each event to reset the containers */
    virtual void Reset();

    /** Sets detector position and sizes */
    void SetZposition(Double_t z) {det_zPos = z;}
    void SetBoxDimensions(Double_t x, Double_t y, Double_t z) {
        xbox_fulldet = x;
        ybox_fulldet = y;
        zbox_fulldet = z;
    }

    /**  Create the detector geometry */
    void ConstructGeometry();

    /**      This method is an example of how to add your own point
     *       of type TimeRpcPoint to the clones array
    */
    UpstreamTaggerPoint* AddHit(Int_t trackID, Int_t detID,
			 TVector3 pos, TVector3 mom,
			 Double_t time, Double_t length,
			 Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom);

    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack() {;}
    virtual void   BeginEvent() {;}

    Double_t module[11][3];  // x,y,z centre positions for each module
    // TODO Avoid 1-indexed array!

    /** Track information to be stored until the track leaves the active volume.*/
    Int_t          fTrackID;            //!  track index
    Int_t          fVolumeID;           //!  volume id
    TLorentzVector fPos;                //!  position at entrance
    TLorentzVector fMom;                //!  momentum at entrance
    Double_t       fTime;               //!  time
    Double_t       fLength;             //!  length
    Double_t       fELoss;              //!  energy loss

    /** Detector parameters.*/

    Double_t     det_zPos;     //!  z-position of detector (set via SetZposition)
    // Detector box dimensions (set via SetBoxDimensions, defaults provided below)
    Double_t xbox_fulldet = 4.4 * m;  //!  X dimension (default: 4.4 m)
    Double_t ybox_fulldet = 6.4 * m;  //!  Y dimension (default: 6.4 m)
    Double_t zbox_fulldet = 16.0 * cm; //!  Z dimension/thickness (default: 16 cm)

  private:

    TGeoVolume* UpstreamTagger_fulldet; // Timing_detector_1 object
    TGeoVolume* scoringPlaneUBText; // new scoring plane
    /** container for data points */
    TClonesArray* fUpstreamTaggerPointCollection;

    UpstreamTagger(const UpstreamTagger&);
    UpstreamTagger& operator=(const UpstreamTagger&);
    Int_t InitMedium(const char* name);


    ClassDef(UpstreamTagger,1)
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGER_H_
