#ifndef PRESTRAWDETECOR_H
#define PRESTRAWDETECOR_H

#include "FairDetector.h"
#include "FairVolume.h"
#include "TVector3.h"
#include "TClonesArray.h"
#include "TLorentzVector.h"

class prestrawdetectorPoint;
class FairVolume;
class TClonesArray;

class prestrawdetector : public FairDetector
{
  public:
    prestrawdetector(const char* name, Bool_t active);
    prestrawdetector();
    virtual ~prestrawdetector();

    /**      Initialization of the detector is done here    */
    virtual void   Initialize(); //done

    virtual Bool_t ProcessHits( FairVolume* v=0);//done

    prestrawdetectorPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss, Int_t pdgCode);
    
    /**       Registers the produced collections in FAIRRootManager.     */
    virtual void   Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const ; //done

    /**      has to be called after each event to reset the containers      */
    virtual void   Reset();

    void SetZ(Double_t z0);

    void ConstructGeometry();
   
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
    Double_t     fPSDz;
    std::string fMedium; 
    Int_t          fTrackID;                //!  track index
    Int_t          fVolumeID;               //!  volume id
    TLorentzVector fPos;                    //!  position at entrance
    TLorentzVector fMom;                    //!  momentum at entrance
    Double_t     fTime;                   //!  time
    Double_t     fLength;                 //!  length
    Double_t     fELoss;
    TClonesArray* fprestrawdetectorPointCollection; // collection of hit points

    prestrawdetector(const prestrawdetector&);
    prestrawdetector& operator=(const prestrawdetector&);

    Int_t InitMedium(const char* name);
    ClassDef(prestrawdetector,2)
};

#endif
