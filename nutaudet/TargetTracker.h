//
//  TargetTracker.h
//  
//
//  Created by Annarita Buonaura on 17/01/15.
//
//

#ifndef TargetTracker_H
#define TargetTracker_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class TTPoint;
class FairVolume;
class TClonesArray;

class TargetTracker : public FairDetector
{
public:
    TargetTracker(const char* name, Double_t TTX, Double_t TTY, Double_t TTZ, Bool_t Active, const char* Title = "TargetTrackers");
    TargetTracker();
    virtual ~TargetTracker();
    
    void ConstructGeometry();
    
    void SetSciFiParam(Double_t scifimat_width_, Double_t scifimat_hor_, Double_t scifimat_vert_, 
                         Double_t scifimat_z_, Double_t support_z_, Double_t honeycomb_z_);
    void SetNumberSciFi(Int_t n_hor_planes_, Int_t n_vert_planes_);
    void SetTargetTrackerParam(Double_t TTX, Double_t TTY, Double_t TTZ);
    void SetBrickParam(Double_t CellW);
    void SetTotZDimension(Double_t Zdim);
    void DecodeTTID(Int_t detID, Int_t &NTT, int &nplane, Bool_t &ishor);
    void SetNumberTT(Int_t n);
    void SetDesign(Int_t Design);

    
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
     */

    TTPoint* AddHit(Int_t trackID, Int_t detID,
			TVector3 pos, TVector3 mom,
			Double_t time, Double_t length,
			Double_t eLoss, Int_t pdgCode);
    
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
    
       
    TargetTracker(const TargetTracker&);
    TargetTracker& operator=(const TargetTracker&);
    
    ClassDef(TargetTracker,4);
    
 private:
    
    /** Track information to be stored until the track leaves the
     active volume.
     */
    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double32_t     fTime;              //!  time
    Double32_t     fLength;            //!  length
    Double32_t     fELoss;             //!  energy loss
    
    /** container for data points */
    TClonesArray*  fTTPointCollection;
    
protected:
    
    Double_t TTrackerX;
    Double_t TTrackerY;
    Double_t TTrackerZ;

    Double_t scifimat_width;
    Double_t scifimat_hor;
    Double_t scifimat_vert;
    Double_t scifimat_z;
    Double_t support_z; 
    Double_t honeycomb_z;
    Int_t n_hor_planes;
    Int_t n_vert_planes;

    Double_t CellWidth; //dimension of the cell containing brick and CES
    Double_t ZDimension; //Dimension of the TTs+bricks total volume
    
    Int_t fNTT; //number of TT

    Int_t fDesign;

    
    Int_t InitMedium(const char* name);
    
};

#endif
