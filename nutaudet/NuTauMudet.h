#ifndef NUTAUMUDET_H
#define NUTAUMUDET_H

#include "FairModule.h"                 // for FairModule
#include "FairDetector.h"                  // for FairDetector

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

#include "TVector3.h"
#include "TLorentzVector.h"

class ShipRpcPoint;
class FairVolume;
class TClonesArray;

class NuTauMudet:public FairDetector
{
  public:
  NuTauMudet(const char* name, const Double_t Zcenter, Bool_t Active, const char* Title="NuTauMudet");
    NuTauMudet();
    virtual ~NuTauMudet();

    void SetDesign(Int_t Design);
    void SetTotDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetFeDimensions(Double_t X, Double_t Y, Double_t Z, Double_t Zthin=0.);
    void SetRpcDimDifferences(Double_t deltax, Double_t deltay);
    void SetRpcDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetRpcStripDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetRpcGasDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetRpcElectrodeDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetRpcPETDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetNFeInArm(Int_t N, Int_t Nthin= 0);
    void SetNRpcInArm(Int_t N);
    void SetNRpcInTagger(Int_t NmuRpc); //for the veto tagger
    void SetZDimensionArm(Double_t Z);
    void SetGapDownstream(Double_t Gap);
    void SetGapMiddle(Double_t Gap);
    void SetMagneticField(Double_t B);
    void SetReturnYokeDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetSmallerYokeDimensions(Double_t X, Double_t Y, Double_t Z);
    void SetCoilParameters(Double_t CoilH, Double_t CoilW, Int_t N, Double_t CoilG);
    void SetSupportTransverseDimensions(Double_t UpperSupportX, Double_t UpperSupportY, Double_t LowerSupportX, Double_t LowerSupportY, Double_t LateralSupportX, Double_t LateralSupportY);
    void SetLateralCutSize(Double_t CutHeight , Double_t CutLength); //lateral triangular cuts
    void SetPillarDimensions(Double_t X, Double_t Y, Double_t Z);

    void ConstructGeometry();
    
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
   
    ShipRpcPoint* AddHit(Int_t trackID, Int_t detID,
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

    void DecodeVolumeID(Int_t detID,int &nARM,int &nRPC);
    
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
    TClonesArray*  fShipRpcPointCollection;
    
    Int_t InitMedium(const char* name);
    
    
    
protected:

    Int_t fDesign;
    Double_t fZcenter; //z distance of the center of the spectrometer in cm from the center of the vacuum tube
    Double_t fXtot;
    Double_t fYtot;
    Double_t fZtot; //Dimension of the whole magnetic spectrometr (1st + 2nd arm + HPTs) alogn beam axis
    Int_t fNFe, fNFethin;
    Int_t fNRpc, fNmuRpc;
    Double_t fXFe;
    Double_t fXRpc;
    Double_t fYFe;
    Double_t fYRpc;
    Double_t fZFe, fZFethin; // Width of the Iron Slabs
    Double_t fZRpc; // Width of the Rpc planes
    Double_t fZArm; // Width of the Spectrometer Arms
    Double_t fGapDown; //distance between the end of the second arm of the spectrometer and the decay vessel
    Double_t fGapMiddle; // distance between the two arms of the spectrometer
    Double_t fField;
    Double_t fXRyoke;
    Double_t fYRyoke;
    Double_t fZRyoke;
    
    //Dimensions of the smaller part of the yoke
    Double_t fXRyoke_s;
    Double_t fYRyoke_s;
    Double_t fZRyoke_s;

    Double_t fCoilGap;
    Double_t fCoilH;
    Double_t fCoilW;
    Int_t fNCoil;
    
    Double_t fdeltax, fdeltay; //different RPC transverse sizes
    //Dimension for detailed RPC simulation:
    Double_t fXStrip;
    Double_t fYStrip;
    Double_t fZStrip;
    Double_t fXPet;
    Double_t fYPet;
    Double_t fZPet;
    Double_t fXEle;
    Double_t fYEle;
    Double_t fZEle;
    Double_t fXGas;
    Double_t fYGas;
    Double_t fZGas;
    Double_t fUpSuppX, fUpSuppY;//Dimensions of iron support structures
    Double_t fLowSuppX, fLowSuppY;
    Double_t fLatSuppX, fLatSuppY; //lateral supports

    Double_t fCutHeight, fCutLength; //Cut dimensions
    //Dimension of steel pillars
    Double_t fPillarX;
    Double_t fPillarY;
    Double_t fPillarZ;


    NuTauMudet(const NuTauMudet&);
    NuTauMudet& operator=(const NuTauMudet&);
    ClassDef(NuTauMudet,6)

};



#endif //NuTauMudet_H

