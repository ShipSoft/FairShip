#ifndef SCIFI_H
#define SCIFI_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"                  // for FairDetector

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class SciFiPoint;
class FairVolume;
class TClonesArray;
const int maxnSciFi = 100; //better to prepare arrays larger, to allow larger number of elements
class SciFi:public FairDetector
{
  public:
    SciFi(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ,Bool_t Active, const char* Title="SciFi");
    SciFi();
    virtual ~SciFi();

    void ConstructGeometry();
    void SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox);
    void SetStationDimensions(Double_t SciFiStationDX, Double_t SciFiStationDY, Double_t SciFiStationDZ);
    void SetStationPositions(Int_t nstation, Double_t posx, Double_t posy, Double_t posz);
    void SetStationNumber(Int_t nSciFistations);

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
    SciFiPoint* AddHit(Int_t trackID, Int_t detID,
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

  private:

    /** Track information to be stored until the track leaves the
      active volume.
      */
    Int_t          fTrackID;           //!  track index
    Int_t          fPdgCode;           //!  pdg code
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double32_t     fTime;              //!  time
    Double32_t     fLength;            //!  length
    Double32_t     fELoss;             //!  energy loss

    /** container for data points */
    TClonesArray*  fSciFiPointCollection;

    Int_t InitMedium(const char* name);



  protected:

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

    Int_t nSciFi;
    Double_t DimZSi;

    Double_t xs[maxnSciFi], ys[maxnSciFi], zs[maxnSciFi];
    Double_t xangle[maxnSciFi], yangle[maxnSciFi], zangle[maxnSciFi];

    SciFi(const SciFi&);
    SciFi& operator=(const SciFi&);
    ClassDef(SciFi,1)

};
#endif
