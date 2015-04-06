/**  hcal.h
 *@author Mikhail Prokudin
 **
 ** Defines the active detector HCAL with geometry coded here.
 **/


#ifndef HCAL_H
#define HCAL_H


#include "hcalPoint.h"
#include "hcalStructure.h"
#include "hcalInf.h"

#include "FairDetector.h"

#include "TClonesArray.h"
#include "TLorentzVector.h"
#include "TVector3.h"

#include <list>

class hcalPoint; 
class FairVolume;
class TGeoTranslation;
class hcalLightMap;

#define kNumberOfHCALSensitiveVolumes 6

class hcal : public FairDetector
{

public:

  /** Default constructor **/
  hcal();


  /** Standard constructor.
   *@param name    detetcor name
   *@param active  sensitivity flag
   **/
  hcal(const char* name, Bool_t active, 
	  const char* fileGeo="hcal.geo");


  /** Destructor **/
  virtual ~hcal();


  /** Virtual method ProcessHits
   **
   ** Defines the action to be taken when a step is inside the
   ** active volume. Creates hcal and adds them to the
   ** collection.
   *@param vol  Pointer to the active volume
   **/
  virtual Bool_t  ProcessHits(FairVolume* vol = NULL);


  /** Virtual method Construct geometry
   **
   ** Constructs the HCAL geometry
   **/
  virtual void ConstructGeometry();

  virtual void EndOfEvent();
  virtual void BeginEvent();
  virtual void Reset();
  virtual void Print() const;
  virtual void CopyClones(TClonesArray* cl1, TClonesArray* cl2, Int_t offset);
  virtual void Register();
  virtual void ChangeHit(hcalPoint* oldHit=NULL);
  virtual void FinishPrimary();

  virtual void Initialize();

  /** Accessor to the hit collection **/                       
  virtual TClonesArray* GetCollection(Int_t iColl) const;
  virtual void SetSpecialPhysicsCuts();
  
  /** Get cell coordinates according
   ** to parameter container **/
  static Bool_t GetCellCoord(Int_t fVolumeID, Float_t &x, Float_t &y, Int_t& section);
  /** Get cell coordinates according
   ** to current hcalInf **/
  static Bool_t GetCellCoordInf(Int_t fVolumeID, Float_t &x, Float_t &y, Int_t& section);
protected:
  hcalPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos,
                       TVector3 mom, Double_t time, Double_t length,
                       Double_t eLoss, Int_t pdgcode);
  hcalPoint* AddLiteHit(Int_t trackID, Int_t detID, Double32_t time, Double32_t eLoss);

private:
  Bool_t FillLitePoint(Int_t volnum);
  void FillWallPoint();
  /** Private method ResetParameters
   **
   ** Resets the private members for the track parameters
   **/
  void ResetParameters();
  void SetHcalCuts(Int_t medium);
  hcalPoint* FindHit(Int_t VolId, Int_t TrackId);

private:
  hcalInf*  fInf;			//!
  Option_t* fDebug;			//!

  /** returns type of volume **/
  Int_t GetVolType(Int_t volnum);
  /** Track information to be stored until the track leaves the
      active volume. **/
  /**  track index **/
  Int_t          fTrackID;           	//!  
  /** volume id **/
  Int_t          fVolumeID;          	//!  
  /** position **/
  TLorentzVector fPos;               	//!  
  /** momentum **/
  TLorentzVector fMom;               	//!  
  /** time **/
  Double32_t     fTime;              	//!
  /** length **/
  Double32_t     fLength;            	//!
  /** energy loss **/
  Double32_t     fELoss;             	//!
  /** **/ 
  Int_t          fPosIndex;          	//!

  /** MC point collection on HCAL wall **/ 
  TClonesArray*  fHcalCollection;	//! 
  /** MC point collection inside HCAL **/ 
  TClonesArray*  fLiteCollection;	//! 
  /** HCAL geometry parameters **/
  /** x,y,z size of outer HCAL box [cm] **/
  Float_t fHcalSize[3];			//!
  /** Use simple geometry.
   ** Try to be as compatible to hcal in physics as possible **/
  Int_t fSimpleGeo;			//!
  /** Just construct guarding volume **/
  Int_t fFastMC;			//!
  /** Size of the HCAL in modules **/
  Int_t fXSize;				//!
  Int_t fYSize;				//!
  /** Position of calorimeter center **/
  Float_t fDX;				//!
  Float_t fDY;				//!
  /** Size of calorimeter module [cm] **/
  Float_t fModuleSize;			//!
  /** Z-position of HCAL from the target [cm] **/
  Float_t fZHcal;			//!
  /** Semiaxises of keeping volume for ecal **/
  Float_t fSemiX;
  Float_t fSemiY;
  /** Name of absorber material/media **/
  TString fAbsorber;			//!
  /** thickness of one lead layer [cm] **/
  Float_t fThicknessAbsorber;		//!
  /** thickness of one scintillator layer [cm] **/
  Float_t fThicknessScin;		//!
  /** thickness of one tyvek layer [cm] **/
  Float_t fThicknessTyvk;		//!
  /** total thickness of one layer [cm] **/
  Float_t fThicknessLayer;		//!
  /** total thickness of steel layer [cm] **/
  Float_t fThicknessSteel;		//!
  /** Thickness of tile edging [cm] **/
  Float_t fEdging;			//!
  /** Radius of holes in the calorimeter [cm] **/
  Float_t fHoleRad;			//!
  /** Radius of fibers in calorimeter [cm] **/
  Float_t fFiberRad;			//!
  /** XY Size of cell **/
  Float_t fXCell;			//!
  Float_t fYCell;			//!
  /** Number of holes in modules  **/
  Int_t fNH;				//!
  Int_t fCF;				//!
  /** Names of light maps **/
  TString fLightMapName;		//!
  /** Light maps **/
  hcalLightMap* fLightMap;		//!
  /** number of layers per module **/
  Int_t   fNLayers;			//!
  /** number of layers in first section **/
  Int_t   fNLayers1;			//!
  /** Lenght of calorimeter module **/
  Float_t fModuleLength;		//!
  /** Max number of HCAL cells **/
  Int_t   fVolIdMax;			//!
  /** Number of first hit for current primary **/
  Int_t fFirstNumber;			//!
  /** Map of volumes in HCAL
   ** fVolArr[0]==code of sensivite wall
   ** fVolArr[4]==code of Lead
   ** fVolArr[3]==code of Tyveec
   ** fVolArr[5]==code of scintillator
   **/
  Int_t fVolArr[kNumberOfHCALSensitiveVolumes];		//!

  /** Construct a raw of modules **/
  TGeoVolume* ConstructRaw(Int_t number);
  /** Construct a module **/
  void ConstructModule();
  /** Construct a tile **/
  void ConstructTile(Int_t material);
  /** Next method for simplified geometry **/
  /** Construct a module **/
  void ConstructModuleSimple();
  /** Construct a tile **/
  void ConstructTileSimple(Int_t material);
  TGeoVolume* fModule;			//! Calorimeter Modules
  TGeoVolume* fScTile;			//! Pb tiles 
  TGeoVolume* fTileEdging;		//! Edging of scintillator tiles 
  TGeoVolume* fPbTile;			//! Scintillator tiles
  TGeoVolume* fTvTile;			//! Tyvek sheets
  TGeoVolume* fHoleVol[3];				//! Hole volume
  TGeoVolume* fFiberVol[3];				//! Fiber volume
  TGeoVolume* fSteelTapes[2];				//! Steel tapes
  TGeoTranslation** fHolePos;		//! Positions of holes
  Int_t fModules;			//! Number of mudules
  std::list<std::pair<Int_t, TGeoVolume*> > fRawNumber;	//! List of constructed raws

  /** Volume ID of calorimeter structure **/
  Int_t fStructureId;			//!
  /** Initialize medium with given name **/
  Int_t InitMedium(const char* name);
  /** Initialize all calorimter media **/
  void InitMedia();

  hcal(const hcal&);
  hcal& operator=(const hcal&);

  ClassDef(hcal,1)
};

inline void hcal::ResetParameters()
{
  fTrackID = fVolumeID = 0;
  fPos.SetXYZM(0.0, 0.0, 0.0, 0.0);
  fMom.SetXYZM(0.0, 0.0, 0.0, 0.0);
  fTime = fLength = fELoss = 0;
  fPosIndex = 0;
};


#endif
