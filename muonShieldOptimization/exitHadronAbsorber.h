// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#ifndef MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
#define MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_

#include "FairDetector.h"
#include "TVector3.h"
#include "TLorentzVector.h"
#include "TGeoVolume.h"
#include "vetoPoint.h"
#include "TNtuple.h"
#include "TFile.h"
#include <map>
#include <vector>

class FairVolume;

class exitHadronAbsorber: public FairDetector
{

  public:

    /**      Name :  Detector Name
     *       Active: kTRUE for active detectors (ProcessHits() will be called)
     *               kFALSE for inactive detectors
    */
    exitHadronAbsorber(const char* Name, Bool_t Active);

    /**      default constructor    */
    exitHadronAbsorber();

    /**       destructor     */
    virtual ~exitHadronAbsorber();

    /**      Initialization of the detector is done here    */
    virtual void   Initialize();

    /**       this method is called for each step during simulation
     *       (see FairMCApplication::Stepping())
    */
    virtual Bool_t ProcessHits( FairVolume* v=0);

    /**       Registers the produced collections in FAIRRootManager.     */
    virtual void   Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const;

    /**      has to be called after each event to reset the containers      */
    virtual void   Reset();

    /**      Update track indices in points after track pruning      */
    void UpdatePointTrackIndices(const std::map<Int_t, Int_t>& indexMap);

    /**      Create the detector geometry        */
    void ConstructGeometry();

    /** The following methods can be implemented if you need to make
     *  any optional action in your detector during the transport.
    */

    virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 ,
                               Int_t offset) {;}
    virtual void   SetSpecialPhysicsCuts() {;}
    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun();
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack();
    virtual void   BeginEvent() {;}

    vetoPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom, Int_t eventId);
    inline void SetEnergyCut(Float_t emax) {EMax=emax;}// min energy to be copied to Geant4
    inline void SetOnlyMuons(){fOnlyMuons=kTRUE;}
    inline void SetOpt4DP(){withNtuple=kTRUE;}
    inline void SkipNeutrinos(){fSkipNeutrinos=kTRUE;}
    inline void SetZposition(Float_t x){fzPos=x;}
    inline void SetVetoPointName(TString nam){fVetoName=nam;}
    inline void SetCylindricalPlane(){fCylindricalPlane=kTRUE;}
    inline void SetUseCaveCoordinates(){fUseCaveCoordinates=kTRUE;}

  private:

    /** Track information to be stored until the track leaves the
    active volume.
    */
    Int_t          fUniqueID;
    Int_t          fEventId;           //!  event index
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double_t     fTime;              //!  time
    Double_t     fLength;            //!  length
    Bool_t fOnlyMuons;  //! flag if only muons should be stored
    Bool_t fSkipNeutrinos;  //! flag if neutrinos should be ignored
    TString fVetoName; //name to save veto collection
    // by default, if fzPos is not set, the positioning is behind the hadron abosorber and the tracks are stopped when they hit the sens plane
    // if fzPos is set and has a reasonable value (below 1E8), then the tracks are not stopped and continue to the last plane after the hadron absorber
    Double_t     fzPos;              //!  zPos, optional
    Bool_t withNtuple;               //! special option for Dark Photon physics studies
    TNtuple* fNtuple;               //!
    Float_t EMax;  //! max energy to transport
    Bool_t fCylindricalPlane;  //! flag if the sensPlane to be created should be cylindrical (by default it is not)
    Bool_t fUseCaveCoordinates;  //! set position from cave rather than from muon shield, default is false

    TFile* fout; //!
    TClonesArray* fElectrons; //!
    Int_t index;
    /** container for data points */
    std::vector<vetoPoint>*  fexitHadronAbsorberPointCollection;
    ClassDef(exitHadronAbsorber, 0)
};

#endif  // MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
