#ifndef SPLITCAL_H
#define SPLITCAL_H

#include "FairDetector.h"

#include "TVector3.h"
#include "TLorentzVector.h"

class splitcalPoint;
class FairVolume;
class TClonesArray;

class splitcal: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    splitcal(const char* Name, Bool_t Active);

    /**      default constructor    */
    splitcal();

    /**       destructor     */
    virtual ~splitcal();

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


    void SetZStart(Double_t ZStart);
    void SetEmpty(Double_t Empty, Double_t BigGap, Double_t ActiveECAL_gas_gap, Double_t first_precision_layer,Double_t second_precision_layer, Double_t third_precision_layer, Double_t num_precision_layers);

    void SetThickness(Double_t ActiveECALThickness, Double_t ActiveHCALThickness, Double_t FilterECALThickness, Double_t FilterECALThickness_first, Double_t FilterHCALThickness, Double_t ActiveECAL_gas_Thickness);

    void SetMaterial(Double_t ActiveECALMaterial, Double_t ActiveHCALMaterial, Double_t FilterECALMaterial, Double_t FilterHCALMaterial);

    void SetNSamplings(Int_t nECALSamplings, Int_t nHCALSamplings, Double_t ActiveHCAL);

    void SetNModules(Int_t nModulesInX, Int_t nModulesInY);

    void SetNStrips(Int_t nStrips);

    void SetStripSize(Double_t stripHalfWidth, Double_t stripHalfLength);
 
    void SetXMax(Double_t xMax);

    void SetYMax(Double_t yMax);


    /**      Create the detector geometry        */
    void ConstructGeometry();



    /**      This method is an example of how to add your own point
     *       of type splitcalPoint to the clones array
    */
    splitcalPoint* AddHit(Int_t trackID, Int_t detID,
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
    Double_t fActiveECALThickness,  fActiveHCALThickness, fFilterECALThickness, xfFilterECALThickness,   fFilterECALThickness_first, fFilterHCALThickness;
    Double_t fActiveECALMaterial,  fActiveHCALMaterial, fFilterECALMaterial, fFilterHCALMaterial;
    Double_t fActiveECAL_gas_gap, fActiveECAL_gas_Thickness;
    Int_t fnECALSamplings, fnHCALSamplings;
    Double_t fActiveHCAL;
    Double_t fZStart;
    Double_t fEmpty,fBigGap; 
    Double_t fXMax;
    Double_t fYMax;
    Double_t ffirst_precision_layer, fsecond_precision_layer, fthird_precision_layer, fnum_precision_layers;
    Int_t fNModulesInX, fNModulesInY;
    Int_t fNStripsPerModule; 
    Double_t fStripHalfWidth, fStripHalfLength;

    /** container for data points */

    TClonesArray*  fsplitcalPointCollection;

    splitcal(const splitcal&);
    splitcal& operator=(const splitcal&);
    Int_t InitMedium(const char* name);

    ClassDef(splitcal,1)
};

#endif //SPLITCAL_H
