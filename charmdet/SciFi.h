#ifndef SCIFI_H
#define SCIFI_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class SciFiPoint;
class FairVolume;
class TClonesArray;

class SciFi:public FairDetector
{
  public:
    SciFi(const char* name, const Double_t BX, const Double_t BY, const Double_t BZ, const Double_t zBox, Bool_t Active, const char* Title = "SciFi");
    SciFi();
    virtual ~SciFi();

    /**      Create the detector geometry        */
    void ConstructGeometry();
    void SetZsize(const Double_t MSsize);
    void SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox,Double_t SZPixel, Double_    t Dim1Short, Double_t Dim1Long);
    void SetSiliconDZ(Double_t SiliconDZ);
    void SetSiliconStationPositions(Int_t nstation, Double_t posx, Double_t posy, Double_t posz);
    void SetSiliconStationAngles(Int_t nstation, Double_t anglex, Double_t angley, Double_t anglez)    ;
    void SetSiliconDetNumber(Int_t nSilicon);

    /**      Initialization of the detector is done here    */
    virtual void Initialize();

    /**  Method called for each step during simulation (see FairMCApplication::Stepping()) */
    virtual Bool_t ProcessHits( FairVolume* v=0);

    /**       Registers the produced collections in FAIRRootManager.     */
    virtual void   Register();

    /** Gets the produced collections */
    virtual TClonesArray* GetCollection(Int_t iColl) const ;

    /**      has to be called after each event to reset the containers      */
    virtual void   Reset();

    /**      How to add your own point of type MuonPoint to the clones array */

    SciFiPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
        Double_t time, Double_t length, Double_t eLoss, Int_t pdgCode);


    virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 , Int_t offset) {;}
    virtual void   SetSpecialPhysicsCuts() {;}
    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack() {;}
    virtual void   BeginEvent() {;}

    /*ensuring it can be written to the geometry file*/
    SciFi(const SciFi&);
    SciFi& operator=(const SciFi&);
    ClassDef(SciFi,1);

    /*Allow onvertion of detector ID in other format*/
    void DecodeVolumeID(Int_t detID,int &nHPT);



  private:

    /** Track information to be stored until the track leaves the active volume. */
    Int_t          fTrackID;           //!  track index
    Int_t          fPdgCode;           //!  PDG code
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

    Double_t Dim1Short, Dim1Long;


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
    Double_t zSizeMS = 0; //dimension of the Magnetic PixelModules volume

    Double_t overlap;
    Double_t DimZPixelBox;

    Int_t nSi;
    Double_t DimZSi;

    Double_t xs[12], ys[12], zs[12];
    Double_t xangle[12], yangle[12], zangle[12];

    PixelModules(const PixelModules&);
    PixelModules& operator=(const PixelModules&);
    ClassDef(PixelModules,1)
};
