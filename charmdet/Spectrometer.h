#ifndef SPECTROMETER_H
#define SPECTROMETER_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"                  // for FairDetector

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class SpectrometerPoint;
class FairVolume;
class TClonesArray;

class Spectrometer:public FairDetector
{
  public:
  Spectrometer(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ,Bool_t Active, const char* Title="Magnetic Spectrometer");
    Spectrometer();
    virtual ~Spectrometer();
      
    void ConstructGeometry();
    void SetZsize(const Double_t MSsize);
    void SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox);
    void SetTransverseSizes(Double_t D1X, Double_t D1Y);
    void SetSiliconDZ(Double_t SiliconDZ);  
    void SetSiliconStationPositions(Int_t nstation, Double_t posx, Double_t posy, Double_t posz);
    void SetSciFiDetPositions(Double_t zSciFi1, Double_t zSciFi2);
    void SetSiliconDetNumber(Int_t nSilicon);
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
     */
    SpectrometerPoint* AddHit(Int_t trackID, Int_t detID,
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

    void DecodeVolumeID(Int_t detID,int &nHPT);
    
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
    TClonesArray*  fSpectrometerPointCollection;
    
    Int_t InitMedium(const char* name);
    
    
    
protected:
    //magnetic field intensity
    Double_t Bfield;

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

    Double_t Dim1Short, Dim1Long;
    Double_t overlap;
    Double_t DimSciFi1X;
    Double_t DimSciFi1Y;
    Double_t DimSciFi2X;
    Double_t DimSciFi2Y;
  /*  Double_t DimZPixelBox;*/

   /* Int_t nSi;*/
    Double_t DimZSi;

 /*   Double_t xs[12], ys[12], zs[12];
    Double_t xangle[12], yangle[12], zangle[12];*/
    
    Double_t zposSciFi1, zposSciFi2;
    
    Spectrometer(const Spectrometer&);
    Spectrometer& operator=(const Spectrometer&);
    ClassDef(Spectrometer,2)

};
#endif 
