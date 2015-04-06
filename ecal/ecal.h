/**  ecal.h
 *@author Mikhail Prokudin
 **
 ** Defines the active detector ECAL with geometry coded here.
 **/


#ifndef ECALDETAILED_H
#define ECALDETAILED_H


#include "ecalPoint.h"
#include "ecalStructure.h"
#include "ecalInf.h"

#include "FairDetector.h"

#include "TClonesArray.h"
#include "TLorentzVector.h"
#include "TVector3.h"

#include <list>

class ecalPoint; 
class FairVolume;
class TGeoTranslation;
class ecalLightMap;

#define kNumberOfECALSensitiveVolumes 6
const Int_t cMaxModuleType=5;

class ecal : public FairDetector
{

public:

  /** Default constructor **/
  ecal();


  /** Standard constructor.
   *@param name    detetcor name
   *@param active  sensitivity flag
   **/
  ecal(const char* name, Bool_t active, 
	  const char* fileGeo="ecal_Detailed.geo");


  /** Destructor **/
  virtual ~ecal();


  /** Virtual method ProcessHits
   **
   ** Defines the action to be taken when a step is inside the
   ** active volume. Creates ecal and adds them to the
   ** collection.
   *@param vol  Pointer to the active volume
   **/
  virtual Bool_t  ProcessHits(FairVolume* vol = NULL);


  /** Virtual method Construct geometry
   **
   ** Constructs the ECAL geometry
   **/
  virtual void ConstructGeometry();

  virtual void EndOfEvent();
  virtual void BeginEvent();
  virtual void Reset();
  virtual void Print() const;
  virtual void CopyClones(TClonesArray* cl1, TClonesArray* cl2, Int_t offset);
  virtual void Register();
  virtual void ChangeHit(ecalPoint* oldHit=NULL);
  virtual void FinishPrimary();

  virtual void Initialize();

  /** Accessor to the hit collection **/                       
  virtual TClonesArray* GetCollection(Int_t iColl) const;
  virtual void SetSpecialPhysicsCuts();
  
  /** Get cell coordinates according
   ** to parameter container **/
  static Bool_t GetCellCoord(Int_t fVolumeID, Float_t &x, Float_t &y, Int_t& tenergy);
  /** Get cell coordinates according
   ** to current ecalInf **/
  static Bool_t GetCellCoordInf(Int_t fVolumeID, Float_t &x, Float_t &y, Int_t& tenergy);
  // Get cell for python
  static Bool_t GetCellCoordForPy(Int_t fVolID, TVector3 &all);
protected:
  ecalPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos,
                       TVector3 mom, Double_t time, Double_t length,
                       Double_t eLoss, Int_t pdgcode);
  ecalPoint* AddLiteHit(Int_t trackID, Int_t detID, Double32_t time, Double32_t eLoss);

private:
  Bool_t FillLitePoint(Int_t volnum);
  void FillWallPoint();
  /** Private method ResetParameters
   **
   ** Resets the private members for the track parameters
   **/
  void ResetParameters();
  void SetEcalCuts(Int_t medium);
  ecalPoint* FindHit(Int_t VolId, Int_t TrackId);

private:
  ecalInf*  fInf;			//!
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

  /** MC point collection on ECAL wall **/ 
  TClonesArray*  fEcalCollection;	//! 
  /** MC point collection inside ECAL **/ 
  TClonesArray*  fLiteCollection;	//! 
  /** ECAL geometry parameters **/
  /** x,y,z size of outer ECAL box [cm] **/
  Float_t fEcalSize[3];			//!
  /** Use simple geometry.
   ** Try to be as compatible to ecal in physics as possible **/
  Int_t fSimpleGeo;			//!
  /** Size of the ECAL in modules **/
  Int_t fXSize;				//!
  Int_t fYSize;				//!
  /** Position of calorimeter center **/
  Float_t fDX;				//!
  Float_t fDY;				//!
  /** Size of calorimeter module [cm] **/
  Float_t fModuleSize;			//!
  /** Z-position of ECAL from the target [cm] **/
  Float_t fZEcal;			//!
  /** Semiaxises of keeping volume for ecal **/
  Float_t fSemiX;
  Float_t fSemiY;
  /** thickness of one lead layer [cm] **/
  Float_t fThicknessLead;		//!
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
  Float_t fXCell[cMaxModuleType];	//!
  Float_t fYCell[cMaxModuleType];	//!
  /** Number of holes in modules  **/
  Int_t fNH[cMaxModuleType];		//!
  Int_t fCF[cMaxModuleType];		//!
  /** Names of light maps **/
  TString fLightMapNames[cMaxModuleType];		//!
  /** Light maps **/
  ecalLightMap* fLightMaps[cMaxModuleType];		//!
  /** number of layers per cell **/
  Int_t   fNLayers;			//!
  /** Lenght of calorimeter module **/
  Float_t fModuleLenght;		//!
  /** scall factor for fCellSize and fThicknessLayer **/
  Float_t fGeoScale;			//!
  /** Number of columns in ECAL1 **/
  Int_t   fNColumns1;			//!
  /** Number of rows in ECAL1 **/
  Int_t   fNRows1;			//!
  /** Number of columns in ECAL2 **/
  Int_t   fNColumns2;			//!
  /** Number of rows in ECAL2 **/
  Int_t   fNRows2;			//!
  /** max number of columns in ECAL1 or ECAL2 **/
  Int_t   fNColumns;			//!
  /** max number of rows in ECAL1 or ECAL2 **/
  Int_t   fNRows;			//!
  /** Max number of ECAL cells **/
  Int_t   fVolIdMax;			//!
  /** Number of first hit for current primary **/
  Int_t fFirstNumber;			//!
  /** Map of volumes in ECAL
   ** fVolArr[0]==code of sensivite wall
   ** fVolArr[1]==code of PS Lead
   ** fVolArr[2]==code of PS Scin
   ** fVolArr[4]==code of Lead
   ** fVolArr[3]==code of Tyveec
   ** fVolArr[5]==code of scintillator
   **/
  Int_t fVolArr[kNumberOfECALSensitiveVolumes];		//!

  /** Construct a raw of modules **/
  TGeoVolume* ConstructRaw(Int_t number);
  /** Construct a module with given type **/
  void ConstructModule(Int_t type);
  /** Construct a cell with given type **/
  void ConstructCell(Int_t type);
  /** Construct a tile with given type **/
  void ConstructTile(Int_t type, Int_t material);
  /** Next method for simplified geometry **/
  /** Construct a module with given type **/
  void ConstructModuleSimple(Int_t type);
  /** Construct a cell with given type **/
  void ConstructCellSimple(Int_t type);
  /** Construct a tile with given type **/
  void ConstructTileSimple(Int_t type, Int_t material);
  TGeoVolume* fModules[cMaxModuleType];			//! Calorimeter Modules
  TGeoVolume* fCells[cMaxModuleType];			//! Calorimeter Cells
  TGeoVolume* fScTiles[cMaxModuleType];			//! Pb tiles 
  TGeoVolume* fTileEdging[cMaxModuleType];		//! Edging of scintillator tiles 
  TGeoVolume* fPbTiles[cMaxModuleType];			//! Scintillator tiles
  TGeoVolume* fTvTiles[cMaxModuleType];			//! Tyvek sheets
  TGeoVolume* fHoleVol[3];				//! Hole volume
  TGeoVolume* fFiberVol[3];				//! Fiber volume
  TGeoVolume* fSteelTapes[2];				//! Steel tapes
  TGeoTranslation** fHolePos[cMaxModuleType];		//! Positions of holes
  Int_t fModulesWithType[cMaxModuleType];		//! Number of mudules with type
  std::list<std::pair<Int_t, TGeoVolume*> > fRawNumber;	//! List of constructed raws

  /** Volume ID of calorimeter structure **/
  Int_t fStructureId;			//!
  /** Initialize medium with given name **/
  Int_t InitMedium(const char* name);
  /** Initialize all calorimter media **/
  void InitMedia();

  ecal(const ecal&);
  ecal& operator=(const ecal&);

  ClassDef(ecal,1)

};

inline void ecal::ResetParameters()
{
  fTrackID = fVolumeID = 0;
  fPos.SetXYZM(0.0, 0.0, 0.0, 0.0);
  fMom.SetXYZM(0.0, 0.0, 0.0, 0.0);
  fTime = fLength = fELoss = 0;
  fPosIndex = 0;
};


#endif
