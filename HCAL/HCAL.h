// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef HCAL_HCAL_H_
#define HCAL_HCAL_H_

#include "FairDetector.h"

#include "TVector3.h"
#include "TLorentzVector.h"
#include <RtypesCore.h>

class HCALPoint;
class FairVolume;
class TClonesArray;

class HCAL: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    HCAL(const char* Name, Bool_t Active);

    /**      default constructor    */
    HCAL();

    /**       destructor     */
    virtual ~HCAL();

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

    void SetMaterial(Bool_t ActiveECALMaterial);

    void SetNSamplings(Int_t nSamplings);

    void SetNmodulesXY(Int_t NmodulesX, Int_t NmodulesY);
    void SetModuleSize(Double_t moduleX, Double_t moduleY);

    void SetPassiveLayerXYZ(Double_t PassiveLayerX, Double_t PassiveLayerY, Double_t PassiveLayerZ);


    void SetNBars(Int_t nBars);

    void SetBarSize(Double_t ScintBarSizeX, Double_t ScintBarSizeY, Double_t ScintBarSizeZ); 

    /**      Create the detector geometry        */
    void ConstructGeometry();



    /**      This method is an example of how to add your own point
     *       of type HCALPoint to the clones array
    */
    HCALPoint* AddHit(Int_t trackID, Int_t detID,
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
    
    Double_t fZStart;
    Double_t fTotalXDim;
    Double_t fTotalYDim;
    Double_t fScintBarX;
    Double_t fScintBarY;
    Double_t fScintBarZ;
    Double_t fPassiveLayerX;
    Double_t fPassiveLayerY;
    Double_t fPassiveLayerZ;
    UShort_t fnSamplings;
    Bool_t fActiveHCALMaterial;
    UInt_t fNBarsPerLayer;
    UShort_t fNmodulesX;
    UShort_t fNmodulesY;
    Double_t fModule_Size_X;
    Double_t fModule_Size_Y;

    /** container for data points */

    TClonesArray*  fHCALPointCollection;

    HCAL(const HCAL&);
    HCAL& operator=(const HCAL&);
    Int_t InitMedium(const char* name);

    ClassDef(HCAL,1)
};

#endif  
