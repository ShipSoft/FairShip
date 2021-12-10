//  
//  Floor.h 
//   
//  by A. Buonaura
// tunnel system from Fluka geometry added, T.Ruf Dec 2020
//
#ifndef Floor_H
#define Floor_H

#include "FairDetector.h"                 // for FairModule
#include "TLorentzVector.h"
#include "Rtypes.h"                     // for Floor::Class, Bool_t, etc
#include "TGeoArb8.h"
#include "TVector3.h"
#include "vetoPoint.h"

#include <string>                       // for string

class FairVolume;
class TClonesArray;

class Floor : public  FairDetector
{
  public:
    Floor(const char* name, Bool_t Active);
    Floor();
    virtual ~Floor();
	void SetConfPar(TString name, Float_t value){conf_floats[name]=value;}
	void SetConfPar(TString name, Int_t value){conf_ints[name]=value;}
	void SetConfPar(TString name, TString value){conf_strings[name]=value;}
	Float_t  GetConfParF(TString name){return conf_floats[name];} 
	Int_t      GetConfParI(TString name){return conf_ints[name];}
	TString  GetConfParS(TString name){return conf_strings[name];}

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

    void ConstructGeometry();

    virtual void   CopyClones( TClonesArray* cl1,  TClonesArray* cl2 ,
                               Int_t offset) {;}
    virtual void   SetSpecialPhysicsCuts() {;}
    virtual void   EndOfEvent();
    virtual void   FinishPrimary() {;}
    virtual void   FinishRun() {;}
    virtual void   BeginPrimary() {;}
    virtual void   PostTrack() {;}
    virtual void   PreTrack();
    virtual void   BeginEvent() {;}

    vetoPoint* AddHit(Int_t trackID, Int_t detID,
                             TVector3 pos, TVector3 mom,
                             Double_t time, Double_t length,
                             Double_t eLoss,Int_t pdgcode,TVector3 Lpos, TVector3 Lmom);

    inline void SetEmin(float E) {fEmin = E;}  // set min  kin energy for tracking
    inline void SetZmax(float Z) {fzPos = Z;}  // set max z position for which energy cut is applied. 
    inline void SetFastMuon() {fFastMuon=true;}  // kill all tracks except of muons
    inline void MakeSensitive() {fMakeSensitive=true;}  // make Tunnel sensitive

   Int_t InitMedium(const char* name);

    TVector3 crossing(TVector3 H1,TVector3 H2,TVector3 H3,TVector3 P1,TVector3 P2,TVector3 P3);
 
private:
	/** configuration parameters **/
	std::map<TString,Float_t> conf_floats;
	std::map<TString,Int_t> conf_ints;
	std::map<TString,TString> conf_strings;

    Int_t          fTrackID;           //!  track index
    Int_t          fVolumeID;          //!  volume id
    TLorentzVector fPos;               //!  position at entrance
    TLorentzVector fMom;               //!  momentum at entrance
    Double_t     fTime;              //!  time
    Double_t     fLength;            //!  length
    Double_t     fzPos;              //!  zPos
    Double_t     fThick;             //!  thickness
    Double_t     fELoss;              //!  
    Double_t     fTotalEloss;         //!  
    TString      fMaterial;           //!  material
    /** container for data points */
    TClonesArray*  fFloorPointCollection;
    Double_t SND_Z; // Position of SND with respect to FLUKA coordinate system origin at IP1
     Bool_t      fFastMuon;              //!
     Float_t     fEmin;                            //!
     Bool_t      fMakeSensitive;      //!
  ClassDef(Floor,2)
};

#endif //Floor_H

