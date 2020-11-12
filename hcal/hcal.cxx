/**  hcal.cxx
 *@author Mikhail Prokudin
 **
 ** Defines the active detector ECAL with geometry coded here.
 ** Layers, holes, fibers,steel tapes implemented 
 **/

#include "hcal.h"

#include "hcalPoint.h"
#include "hcalLightMap.h"

#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoNode.h"
#include "FairGeoRootBuilder.h"
#include "FairRuntimeDb.h"
#include "FairRootManager.h"
#include "FairRun.h"
#include "FairRunAna.h"
#include "ShipStack.h"
#include "FairVolume.h"
#include "FairGeoMedium.h"
#include "FairGeoMedia.h"

#include "TClonesArray.h"
#include "TGeoMCGeometry.h"
#include "TGeoManager.h"
#include "TParticle.h"
#include "TVirtualMC.h"
#include "TGeoBBox.h"
#include "TGeoPgon.h"
#include "TGeoTube.h"
#include "TGeoMatrix.h"
#include "TList.h"

#include <iostream>
#include <stdlib.h>

using namespace std;

#define kN kNumberOfHCALSensitiveVolumes

// -----   Default constructor   -------------------------------------------
hcal::hcal() 
  : FairDetector("HCAL", kTRUE, khcal),
    fInf(NULL),
    fDebug(NULL),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1.),
    fPosIndex(0),
    fHcalCollection(new TClonesArray("hcalPoint")),
    fLiteCollection(new TClonesArray("hcalPoint")),
    fHcalSize(),
    fSimpleGeo(0),
    fFastMC(0),
    fXSize(0),
    fYSize(0),
    fDX(0.),
    fDY(0.),
    fModuleSize(0.),
    fZHcal(0.),
    fSemiX(0.),
    fSemiY(0.),
    fAbsorber("Lead"),
    fThicknessAbsorber(0.),
    fThicknessScin(0.),
    fThicknessTyvk(0.),
    fThicknessLayer(0.),
    fThicknessSteel(0.),
    fEdging(0.),
    fHoleRad(0.),
    fFiberRad(0.),
    fXCell(0),
    fYCell(0),
    fNH(0),
    fCF(0),
    fLightMapName(""),
    fLightMap(NULL),
    fNLayers(0),
    fModuleLength(0.),
    fVolIdMax(0),
    fFirstNumber(0),
    fVolArr(),
    fModule(NULL),
    fScTile(NULL),
    fTileEdging(NULL),
    fPbTile(NULL),
    fTvTile(NULL),
    fHoleVol(),
    fFiberVol(),
    fSteelTapes(),
    fHolePos(),
    fModules(0),
    fRawNumber(),
    fStructureId(0)
{
  fVerboseLevel = 1;

  Int_t i;

  for(i=kN-1;i>-1;i--)
    fVolArr[i]=-1111;
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
hcal::hcal(const char* name, Bool_t active, const char* fileGeo)
  : FairDetector(name, active, khcal),
    fInf(NULL),
    fDebug(NULL),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1.),
    fPosIndex(0),
    fHcalCollection(new TClonesArray("hcalPoint")),
    fLiteCollection(new TClonesArray("hcalPoint")),
    fHcalSize(),
    fSimpleGeo(0),
    fFastMC(0),
    fXSize(0),
    fYSize(0),
    fDX(0.),
    fDY(0.),
    fModuleSize(0.),
    fZHcal(0.),
    fSemiX(0.),
    fSemiY(0.),
    fAbsorber("Lead"),
    fThicknessAbsorber(0.),
    fThicknessScin(0.),
    fThicknessTyvk(0.),
    fThicknessLayer(0.),
    fThicknessSteel(0.),
    fEdging(0.),
    fHoleRad(0.),
    fFiberRad(0.),
    fXCell(0),
    fYCell(0),
    fNH(0),
    fCF(0),
    fLightMapName(""),
    fLightMap(NULL),
    fNLayers(0),
    fModuleLength(0.),
    fVolIdMax(0),
    fFirstNumber(0),
    fVolArr(),
    fModule(NULL),
    fScTile(NULL),
    fTileEdging(NULL),
    fPbTile(NULL),
    fTvTile(NULL),
    fHoleVol(),
    fFiberVol(),
    fSteelTapes(),
    fHolePos(),
    fModules(0),
    fRawNumber(),
    fStructureId(0)  
{
  /** hcal constructor:
   ** reads geometry parameters from the ascii file <fileGeo>,
   ** creates the ECAL geometry container hcalInf
   ** and initializes basic geometry parameters needed to construct
   ** TGeo geometry
   **/

  fVerboseLevel=0;
  Int_t i;
  Int_t j;
  TString nm;
  Info("hcal","Geometry is read from file %s.", fileGeo);
  fInf=hcalInf::GetInstance(fileGeo);
  if (fInf==NULL)
  {
    Fatal("hcal"," Can't read geometry from %s.", fileGeo);
    return;
  }
  fHcalSize[0]=fInf->GetHcalSize(0);
  fHcalSize[1]=fInf->GetHcalSize(1);
  fHcalSize[2]=fInf->GetHcalSize(2);

  fZHcal=fInf->GetZPos();

  fThicknessAbsorber=fInf->GetAbsorber();
  fThicknessScin=fInf->GetScin();
  fThicknessTyvk=fInf->GetTyveec();
  fNLayers=fInf->GetNLayers();

  fXSize=fInf->GetXSize();
  fYSize=fInf->GetYSize();
  
  fPosIndex=0;
  fDebug="";

  fSemiX=fInf->GetVariableStrict("xsemiaxis");
  fSemiY=fInf->GetVariableStrict("ysemiaxis");
  fHoleRad=fInf->GetVariableStrict("holeradius");
  fFiberRad=fInf->GetVariableStrict("fiberradius");
  fThicknessSteel=fInf->GetVariableStrict("steel");
  fEdging=fInf->GetVariableStrict("tileedging");
  fModuleSize=fInf->GetVariableStrict("modulesize");
  fSimpleGeo=(Int_t)fInf->GetVariableStrict("usesimplegeo");
  fFastMC=(Int_t)fInf->GetVariableStrict("fastmc");
  fDX=fInf->GetVariableStrict("xpos");
  fDY=fInf->GetVariableStrict("ypos");
  fNLayers1=fInf->GetN1Layers();

  for(i=kN-1;i>-1;i--)
    fVolArr[i]=-1111;

  for(i=0;i<2;i++)
  {
    fSteelTapes[i]=NULL;
  }
  for(i=0;i<3;i++)
  {
    fHoleVol[i]=NULL;
    fFiberVol[i]=NULL;
  }
  /** Counting modules **/
  for(i=0;i<fInf->GetXSize();i++)
  for(j=0;j<fInf->GetYSize();j++)
  {
    if (fInf->GetType(i,j)==0) continue;
    if (fInf->GetType(i,j)==1)
      fModules++;
    else
      Fatal("hcal", "Wrong module type");
  }

  fCF=(Int_t)fInf->GetVariableStrict("cf");
  fNH=(Int_t)fInf->GetVariableStrict("nh");
  fLightMapName=fInf->GetStringVariable("lightmap");
  if (fLightMapName!="none")
    fLightMap=new hcalLightMap(fLightMapName, nm);
  else
    fLightMap=NULL;
  fAbsorber=fInf->GetStringVariable("absorbermaterial");
  Info("hcal", "Number of modules is %d, lightmap %s", fModules, fLightMapName.Data());
  fXCell=(fModuleSize-2.0*fThicknessSteel)-2.0*fEdging;
  fYCell=(fModuleSize-2.0*fThicknessSteel)-2.0*fEdging;
  Info("hcal", "Size of cell of type %d is %f cm.", i, fXCell);
}

// -------------------------------------------------------------------------

void hcal::Initialize()
{
  FairDetector::Initialize();
/*
  FairRun* sim = FairRun::Instance();
  FairRuntimeDb* rtdb=sim->GetRuntimeDb();
  CbmGeoHcalPar *par=new CbmGeoHcalPar();
//  fInf->FillGeoPar(par,0);
  rtdb->addContainer(par);
*/
}

// -----   Destructor   ----------------------------------------------------
hcal::~hcal()
{
  if (fHcalCollection) {
    fHcalCollection->Delete(); 
    delete fHcalCollection;
    fHcalCollection=NULL;
  }
  if (fLiteCollection) {
    fLiteCollection->Delete();
    delete fLiteCollection;
    fLiteCollection=NULL;
  }
}
// -------------------------------------------------------------------------

// -----   Private method SetHcalCuts   ------------------------------------
void hcal::SetHcalCuts(Int_t medium)
{
  /** Set GEANT3 tracking energy cuts for selected medium **/
  if (fInf->GetElectronCut() > 0) {
    gMC->Gstpar(medium,"CUTGAM",fInf->GetElectronCut());
    gMC->Gstpar(medium,"CUTELE",fInf->GetElectronCut());
    gMC->Gstpar(medium,"BCUTE" ,fInf->GetElectronCut());
    gMC->Gstpar(medium,"BCUTM" ,fInf->GetElectronCut());
  }

  if (fInf->GetHadronCut() > 0) {
    gMC->Gstpar(medium,"CUTNEU",fInf->GetHadronCut());
    gMC->Gstpar(medium,"CUTHAD",fInf->GetHadronCut());
    gMC->Gstpar(medium,"CUTMUO",fInf->GetHadronCut());
//    gMC->Gstpar(medium,"PPCUTM",fInf->GetHadronCut());
  }
  ;
}
// -------------------------------------------------------------------------

void hcal::FinishPrimary()
{
  fFirstNumber=fLiteCollection->GetEntriesFast();
}

//_____________________________________________________________________________
void hcal::ChangeHit(hcalPoint* oldHit)
{
  Double_t edep = fELoss;
  Double_t el=oldHit->GetEnergyLoss();
  Double_t ttime=gMC->TrackTime()*1.0e9;
  oldHit->SetEnergyLoss(el+edep);
  if(ttime<oldHit->GetTime())
    oldHit->SetTime(ttime);
}

//_____________________________________________________________________________
void hcal::SetSpecialPhysicsCuts()
{
  FairRun* fRun = FairRun::Instance();
//  if (strcmp(fRun->GetName(),"TGeant3") == 0)
  {
    Int_t mediumID;
    mediumID = gGeoManager->GetMedium("Scintillator")->GetId();
    SetHcalCuts(mediumID);
    mediumID = gGeoManager->GetMedium(fAbsorber)->GetId();
    SetHcalCuts(mediumID);
    mediumID = gGeoManager->GetMedium("Tyvek")->GetId();
    SetHcalCuts(mediumID);
    mediumID = gGeoManager->GetMedium("SensVacuum")->GetId();
    SetHcalCuts(mediumID);
    mediumID = gGeoManager->GetMedium("ECALAir")->GetId();
    SetHcalCuts(mediumID);
    mediumID = gGeoManager->GetMedium("ECALFiber")->GetId();
    SetHcalCuts(mediumID);
    mediumID = gGeoManager->GetMedium("ECALTileEdging")->GetId();
    SetHcalCuts(mediumID);
    mediumID = gGeoManager->GetMedium("ECALSteel")->GetId();
    SetHcalCuts(mediumID);
  }
}
// -----   Public method ProcessHits  --------------------------------------
Bool_t  hcal::ProcessHits(FairVolume* vol)
{
  /** Fill MC point for sensitive ECAL volumes **/
  TString Hcal="Hcal";
  fELoss   = gMC->Edep();
  fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
  fTime    = gMC->TrackTime()*1.0e09;
  fLength  = gMC->TrackLength();

  //if (vol->getVolumeId()==fStructureId) {
  if (Hcal.CompareTo(gMC->CurrentVolName())==0) {
    if (gMC->IsTrackEntering()) {
      FillWallPoint();
      ((ShipStack*)gMC->GetStack())->AddPoint(khcal, fTrackID);
  
      ResetParameters();

      return kTRUE;
    } else {
      return kFALSE;
    }
  }

  if (fELoss<=0) return kFALSE;

  if (fELoss>0)
  {
    Int_t i;
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Double_t x, y, z;
    Double_t px;
    Double_t py;
    Double_t dx;
    Int_t mx;
    Int_t my;
    Int_t type;
    Int_t cx;
    Int_t cy;
    Int_t layer;
    gMC->TrackPosition(x, y, z);
//    cout << "Id: " << p->GetPdgCode() << " (" << x << ", " << y << ", ";
//    cout << z << "): ";
//    cout << endl;
/*
    for(i=0;i<10;i++)
    {
      gMC->CurrentVolOffID(i, mx); cout << i << ":" << mx << ", ";
    }
    cout << endl;
*/
    if (fSimpleGeo==0)
    {
      gMC->CurrentVolOffID(1, layer); layer--;
      gMC->CurrentVolOffID(2, mx); mx--;
      gMC->CurrentVolOffID(3, my); my--;
    }
    else
    {
      gMC->CurrentVolOffID(0, layer); layer--;
      gMC->CurrentVolOffID(1, mx); mx--;
      gMC->CurrentVolOffID(2, my); my--;
    }
    Int_t id=(my*100+mx)*10;
    if (layer>fNLayers1) id++;
//    cout << mx << "(" << x << "), " << my << "(" << y << "), layer="<< layer << endl;
/*   
    Float_t rx; Float_t ry; Int_t ten;
    GetCellCoordInf(id, rx, ry, ten); rx--; ry--;
    type=fInf->GetType(mx, my);
    Float_t d=fInf->GetVariableStrict("modulesize")/type;
    if (x>rx-0.001&&x<rx+d+0.001&&y>ry-0.001&&y<ry+d+0.001) 
    {
//      cout << "+++ ";
      ;
    }
    else
    {
      cout << mx << ", " << my << ", " << cell << endl;
      cout << "--- ";
      cout << "(" << x << ", " << y << ") : (" << rx << ", " << ry << ")" << endl; 
    }
*/
    fVolumeID=id;
    if (fSimpleGeo==0)
    {
      // An old version
      // px=mx*fModuleSize-fHcalSize[0]/2.0+cx*fModuleSize/type;
      // py=my*fModuleSize-fHcalSize[1]/2.0+cy*fModuleSize/type;
      // With correction for steel tapes and edging
      // TODO: Check this
      px=mx*fModuleSize-fHcalSize[0]/2.0+fEdging+fThicknessSteel;
      py=my*fModuleSize-fHcalSize[1]/2.0+fEdging+fThicknessSteel;

      px=(x-px)/fXCell;
      py=(y-py)/fYCell;
      if (px>=0&&px<1&&py>=0&&py<1)
      {
        fELoss*=fLightMap->Data(px-0.5, py-0.5);
        FillLitePoint(0);
      }
    }
    else
      FillLitePoint(0);
//    for(i=0;i<8;i++)
//    {
//      Int_t t;
//      
//      gMC->CurrentVolOffID(i, t);
//      cout << i << ": " << gMC->CurrentVolOffName(i) << " " << t << "; ";
//   }
//    cout << endl;
  }
  ((ShipStack*)gMC->GetStack())->AddPoint(khcal, fTrackID);
  
  ResetParameters();

  return kTRUE;

}

/** returns type of volume **/
Int_t hcal::GetVolType(Int_t volnum)
{
	Int_t i;
	for(i=kN-1;i>-1;i--) {
	  if (fVolArr[i]==volnum) break;
	}
        
	return i;
}

//-----------------------------------------------------------------------------
void hcal::FillWallPoint()
{
  /** Fill MC points on the ECAL front wall **/

  gMC->TrackPosition(fPos);
  gMC->TrackMomentum(fMom);
  fVolumeID = -1;
  Double_t mass = gMC->TrackMass();
  // Calculate kinetic energy
  Double_t ekin = TMath::Sqrt( fMom.Px()*fMom.Px() +
			       fMom.Py()*fMom.Py() +
			       fMom.Pz()*fMom.Pz() +
			       mass * mass ) - mass;
  fELoss = ekin;
  // Create hcalPoint at the entrance of calorimeter
  // for particles with pz>0 coming through the front wall
  if (fMom.Pz() > 0 && fPos.Z() < fZHcal+0.01)
  {
    TParticle* part=((ShipStack*)gMC->GetStack())->GetParticle(fTrackID);
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
	   TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, 
	   fELoss, part->GetPdgCode());
  }
  fTrackID=gMC->GetStack()->GetCurrentTrackNumber();
}

hcalPoint* hcal::FindHit(Int_t VolId, Int_t TrackId)
{
  for(Int_t i=fFirstNumber;i<fLiteCollection->GetEntriesFast();i++)
  {
    hcalPoint* point=(hcalPoint*)fLiteCollection->At(i);
    if (point->GetTrackID()==TrackId&&point->GetDetectorID()==VolId)
      return point;
  }
  return NULL;
}
//-----------------------------------------------------------------------------
Bool_t hcal::FillLitePoint(Int_t volnum)
{
  /** Fill MC points inside the ECAL for non-zero deposited energy **/

  //Search for input track
  
  static Float_t zmin=fZHcal-0.0001;
  static Float_t zmax=fZHcal+fHcalSize[2];
  static Float_t xhcal=fHcalSize[0]/2;
  static Float_t yhcal=fHcalSize[1]/2;
  TParticle* part=gMC->GetStack()->GetCurrentTrack();
  fTrackID=gMC->GetStack()->GetCurrentTrackNumber();

// cout << zmin << " : " << zmax << " : " << xhcal << ", " << yhcal << endl;
// cout << part->GetFirstMother() << " : " << part->Vx() << ", " << part->Vy() << ", " << part->Vz() << endl;
  /** Need to rewrite this part **/
  while (part->GetFirstMother()>=0&&part->Vz()>=zmin&&part->Vz()<=zmax&&TMath::Abs(part->Vx())<=xhcal&&TMath::Abs(part->Vy())<=yhcal)
    {
      fTrackID=part->GetFirstMother();
      part =((ShipStack*)gMC->GetStack())->GetParticle(fTrackID);
//      cout << "-> " << part->GetFirstMother() << " : " << part->Vx() << ", " << part->Vy() << ", " << part->Vz() << endl;
    }
//  if (part->Vz()>500)
//    cout << part->Vx() << ", " << part->Vy() << ", " << part->Vz() << endl;
#ifdef _DECAL
  if (fTrackID<0) cout<<"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!fTrackID="<<fTrackID<<endl;
#endif
  hcalPoint* oldHit;
  hcalPoint* newHit;
  
  if ((oldHit=FindHit(fVolumeID,fTrackID))!=NULL)
    ChangeHit(oldHit);
  else
    // Create hcalPoint for scintillator volumes
    newHit = AddLiteHit(fTrackID, fVolumeID, fTime, fELoss);
      

  return kTRUE;
}

// -----   Public method EndOfEvent   --------------------------------------
void hcal::EndOfEvent() {
  if (fVerboseLevel) Print();
  fHcalCollection->Clear();

  fLiteCollection->Clear();
  fPosIndex = 0;
  fFirstNumber=0;
}
// -------------------------------------------------------------------------

// -----   Public method GetCollection   -----------------------------------
TClonesArray* hcal::GetCollection(Int_t iColl) const
{
  if (iColl == 0) return fHcalCollection;
  if (iColl == 1) return fLiteCollection;
  else return NULL;
}
// -------------------------------------------------------------------------

// -----   Public method Reset   -------------------------------------------
void hcal::Reset()
{
  fHcalCollection->Clear();
  fLiteCollection->Clear();
  ResetParameters();
  fFirstNumber=0;
}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void hcal::Print() const 
{
  Int_t nHits = fHcalCollection->GetEntriesFast();
  Int_t nLiteHits;
  Int_t i;

  cout << "-I- hcal: " << nHits << " points registered in this event.";
  cout << endl;

  nLiteHits=fLiteCollection->GetEntriesFast();
  cout << "-I- hcal: " << nLiteHits << " lite points registered in this event.";
  cout << endl;

  if (fVerboseLevel>1)
  {
    for (i=0;i<nHits;i++)
      (*fHcalCollection)[i]->Print();
    for (i=0;i<nLiteHits;i++)
      (*fLiteCollection)[i]->Print();
  }
}
// -------------------------------------------------------------------------

// -----   Public method CopyClones   --------------------------------------
void hcal::CopyClones(TClonesArray* cl1, TClonesArray* cl2, Int_t offset)
{   
  Int_t nEntries = cl1->GetEntriesFast();
  Int_t i;
  Int_t index;
  cout << "-I- hcal: " << nEntries << " entries to add." << endl;
  TClonesArray& clref = *cl2;
  if (cl1->GetClass()==hcalPoint::Class()) {
    hcalPoint* oldpoint = NULL;
    for (i=0; i<nEntries; i++) {
      oldpoint = (hcalPoint*) cl1->At(i);
      index = oldpoint->GetTrackID()+offset;
      oldpoint->SetTrackID(index);
      new (clref[fPosIndex]) hcalPoint(*oldpoint);
      fPosIndex++;
    }
    cout << "-I- hcal: " << cl2->GetEntriesFast() << " merged entries."
         << endl;
  }
  else if (cl1->GetClass()==hcalPoint::Class()) {
    hcalPoint* oldpoint = NULL;
    for (i=0; i<nEntries; i++) {
      oldpoint = (hcalPoint*) cl1->At(i);
      index = oldpoint->GetTrackID()+offset;
      oldpoint->SetTrackID(index);
      new (clref[fPosIndex]) hcalPoint(*oldpoint);
      fPosIndex++;
    }
    cout << "-I- hcal: " << cl2->GetEntriesFast() << " merged entries."
         << endl;
  }
}
// -------------------------------------------------------------------------

// -----   Public method Register   ----------------------------------------
void hcal::Register()
{
  FairRootManager::Instance()->Register("HcalPoint","Hcal",fHcalCollection,kTRUE);
  FairRootManager::Instance()->Register("HcalPointLite","HcalLite",fLiteCollection,kTRUE);
  ;
}
// -------------------------------------------------------------------------

// -----   Public method ConstructGeometry   -------------------------------
void hcal::ConstructGeometry()
{
  FairGeoLoader*geoLoad = FairGeoLoader::Instance();
  FairGeoInterface *geoFace = geoLoad->getGeoInterface();
  FairGeoMedia *Media =  geoFace->getMedia();
  FairGeoBuilder *geobuild=geoLoad->getGeoBuilder();

  TGeoVolume *top=gGeoManager->GetTopVolume();

  // cout << top->GetName() << endl;
  TGeoVolume *volume;
  FairGeoMedium *CbmMedium;
  TGeoPgon *spl;

  Float_t *buf = 0;
  Int_t i;
  Double_t par[10];
  Float_t y;
  TString nm;
  Double_t thickness=fThicknessAbsorber+fThicknessScin+fThicknessTyvk*2;
  Double_t moduleth=thickness*fNLayers;
//  Float_t sumWeight;
//  Int_t i;

  // create SensVacuum which is defined in the media file

  /** Initialize all media **/
  InitMedia();
  par[0]=fSemiX;
  par[1]=fSemiY;
  par[2]=fHcalSize[2]/2.0;

  if (!IsActive()){
   Double_t fudgeFactor = 6.34 / 13.7 ; // to have same interaction length as before
   par[2] = par[2]*fudgeFactor;
   volume=gGeoManager->Volume("Hcal", "BOX",  gGeoManager->GetMedium("iron")->GetId(), par, 3);
   gGeoManager->Node("Hcal", 1, top->GetName(), 0.0,0.0, fZHcal, 0, kTRUE, buf, 0);
   return;
  }

  volume=gGeoManager->Volume("Hcal", "BOX",  gGeoManager->GetMedium("SensVacuum")->GetId(), par, 3);
  gGeoManager->Node("Hcal", 1, top->GetName(), 0.0,0.0, fZHcal, 0, kTRUE, buf, 0);
  volume->SetVisLeaves(kTRUE);
  volume->SetVisContainers(kFALSE);
  volume->SetVisibility(kFALSE);


  AddSensitiveVolume(volume);
  fStructureId=volume->GetNumber();

  if (fFastMC==0)
  {
    if (fSimpleGeo==0)
      ConstructModule();
     else
      ConstructModuleSimple();

    TGeoVolume* vol=new TGeoVolumeAssembly("HcalStructure");
//To suppress warring
    vol->SetMedium(gGeoManager->GetMedium("SensVacuum"));
    for(i=0;i<fYSize;i++)
    {
      volume=ConstructRaw(i);
      if (volume==NULL) 
      {
        continue;
      }
      nm=volume->GetName();
      y=(i-fYSize/2.0+0.5)*fModuleSize;
      gGeoManager->Node(nm.Data(), i+1, "HcalStructure", 0.0, y, 0.0, 0, kTRUE, buf, 0);
    }
//TODO:
//Should move the guarding volume, not structure itself
    gGeoManager->Node("HcalStructure", 1, "Hcal", fDX, fDY, 0.0, 0, kTRUE, buf, 0);
  }
}
// -------------------------------------------------------------------------

// ----- Public method ConstructRaw ----------------------------------------
TGeoVolume* hcal::ConstructRaw(Int_t num)
{
  Int_t i;
  list<pair<Int_t, TGeoVolume*> >::const_iterator p=fRawNumber.begin();
  pair<Int_t, TGeoVolume*> out;
  Float_t x;
  Float_t* buf=NULL;
  for(i=0;i<fXSize;i++)
    if ((Int_t)fInf->GetType(i, num)!=0) break;
  if (i==fXSize)
    return NULL;
  for(;p!=fRawNumber.end();++p)
  {
    for(i=0;i<fXSize;i++)
      if (fInf->GetType(i, num)!=fInf->GetType(i, (*p).first))
	break;
    if (i==fXSize)
      break;
  }
  if (p!=fRawNumber.end())
    return (*p).second;
  TString nm="HCALRaw"; nm+=num;
  TString md;
  TGeoVolume* vol=new TGeoVolumeAssembly(nm);
//To suppress warring
  vol->SetMedium(gGeoManager->GetMedium("SensVacuum"));
  for(i=0;i<fXSize;i++)
  {
    x=(i-fXSize/2.0+0.5)*fModuleSize;
    if (fInf->GetType(i, num)==0) continue;
    md="HcalModule";
    gGeoManager->Node(md.Data(),i+1, nm.Data(), x, 0.0, 0.0, 0, kTRUE, buf, 0);
  }

  out.first=num;
  out.second=vol;
  fRawNumber.push_back(out);
  return out.second;
}
// -------------------------------------------------------------------------


// ----- Public method BeginEvent  -----------------------------------------
void hcal::BeginEvent()
{
  ;
}
// -------------------------------------------------------------------------


// -------------------------------------------------------------------------

// -----   Private method AddHit   -----------------------------------------    
hcalPoint* hcal::AddHit(Int_t trackID, Int_t detID, TVector3 pos,         
			      TVector3 mom, Double_t time, Double_t length,       
			      Double_t eLoss, Int_t pdgcode)
{
  TClonesArray& clref = *fHcalCollection;
  Int_t size = clref.GetEntriesFast();
  return new(clref[size]) hcalPoint(trackID, detID, pos, mom,
                                      time, length, eLoss, pdgcode);
}                                                                               
// -------------------------------------------------------------------------

// -----   Private method AddHit   -----------------------------------------    
hcalPoint* hcal::AddLiteHit(Int_t trackID, Int_t detID, Double32_t time, Double32_t eLoss)
{
  TClonesArray& clref = *fLiteCollection;
  Int_t size = clref.GetEntriesFast();
  return new(clref[size]) hcalPoint(trackID, detID, time, eLoss);
}
// -------------------------------------------------------------------------

// -----   Private method ConstructModule ----------------------------------    
void hcal::ConstructModule()
{
  if (fModule!=NULL) return;

  ConstructTile(0);
  ConstructTile(1);
  if (fThicknessTyvk>0) ConstructTile(2);

  TString nm="HcalModule";
  TString nm1;
  TString cellname="HcalCell";
  TString scin="ScTile";
  TString lead="LeadTile";
  TString tyvek="TvTile";
  Int_t i;
  Int_t j;
  Int_t n;
  Float_t x;
  Float_t y;
  Float_t* buf=NULL;
  Double_t thickness=fThicknessAbsorber+fThicknessScin+fThicknessTyvk*2;
  Double_t moduleth=thickness*fNLayers;
  Double_t par[3]={fModuleSize/2.0, fModuleSize/2.0, moduleth/2.0};

  if (fSteelTapes[0]==NULL)
  {
    TGeoBBox* st1=new TGeoBBox(fThicknessSteel/2.0, fModuleSize/2.0-fThicknessSteel, moduleth/2.0);
    nm1="HcalModuleSteelTape1";
    fSteelTapes[0]=new TGeoVolume(nm1.Data(), st1, gGeoManager->GetMedium("ECALSteel"));
  }
  if (fSteelTapes[1]==NULL)
  {
    TGeoBBox* st2=new TGeoBBox(fModuleSize/2.0-fThicknessSteel, fThicknessSteel/2.0, moduleth/2.0);
    nm1="HcalModuleSteelTape2";
    fSteelTapes[1]=new TGeoVolume(nm1.Data(), st2, gGeoManager->GetMedium("ECALSteel"));
  }


//  TGeoVolume* modulev=new TGeoVolumeAssembly(nm);
  TGeoVolume* modulev=gGeoManager->Volume(nm.Data(), "BOX",  gGeoManager->GetMedium("ECALAir")->GetId(), par, 3);
  modulev->SetLineColor(kOrange+3);
  for(i=0;i<fNLayers;i++)
  {
    gGeoManager->Node(scin.Data(), i+1, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin/2.0+i*thickness, 0, kTRUE, buf, 0);
    gGeoManager->Node(lead.Data(), i+1, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin+i*thickness+fThicknessTyvk+fThicknessAbsorber/2.0, 0, kTRUE, buf, 0);
    if (fThicknessTyvk>0.0)
    {
      gGeoManager->Node(tyvek.Data(), 2*i+1, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin+i*thickness+1.5*fThicknessTyvk+fThicknessAbsorber, 0, kTRUE, buf, 0);
      gGeoManager->Node(tyvek.Data(), 2*i+2, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin+i*thickness+0.5*fThicknessTyvk, 0, kTRUE, buf, 0);
    }
  }

  nm1="HcalModuleSteelTape1";
  gGeoManager->Node(nm1.Data(), 1, nm.Data(), -fThicknessSteel/2.0+fModuleSize/2.0, 0.0, 0.0, 0, kTRUE, buf, 0);
  gGeoManager->Node(nm1.Data(), 2, nm.Data(), +fThicknessSteel/2.0-fModuleSize/2.0, 0.0, 0.0, 0, kTRUE, buf, 0);
  nm1="HcalModuleSteelTape2";
  gGeoManager->Node(nm1.Data(), 1, nm.Data(), 0.0, -fThicknessSteel/2.0+fModuleSize/2.0, 0.0, 0, kTRUE, buf, 0);
  gGeoManager->Node(nm1.Data(), 2, nm.Data(), 0.0, +fThicknessSteel/2.0-fModuleSize/2.0, 0.0, 0, kTRUE, buf, 0);

  fModuleLength=moduleth;
  fModule=modulev;
}
// -------------------------------------------------------------------------

// -----   Private method ConstructModuleSimple-----------------------------    
void hcal::ConstructModuleSimple()
{
  if (fModule!=NULL) return;

  ConstructTileSimple(0);
  ConstructTileSimple(1);
  if (fThicknessTyvk>0) ConstructTileSimple(2);

  TString nm="HcalModule";
  TString nm1;
  TString cellname="HcalCell";
  TString scin="ScTile";
  TString lead="LeadTile";
  TString tyvek="TvTile";
  Int_t i;
  Int_t j;
  Int_t n;
  Float_t x;
  Float_t y;
  Float_t* buf=NULL;
  Double_t thickness=fThicknessAbsorber+fThicknessScin+fThicknessTyvk*2;
  Double_t moduleth=thickness*fNLayers;
  Double_t par[3]={fModuleSize/2.0, fModuleSize/2.0, moduleth/2.0};

//  TGeoVolume* modulev=new TGeoVolumeAssembly(nm);
  TGeoVolume* modulev=gGeoManager->Volume(nm.Data(), "BOX",  gGeoManager->GetMedium("ECALAir")->GetId(), par, 3);
  modulev->SetLineColor(kOrange+3);
  for(i=0;i<fNLayers;i++)
  {
    gGeoManager->Node(scin.Data(), i+1, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin/2.0+i*thickness, 0, kTRUE, buf, 0);
    gGeoManager->Node(lead.Data(), i+1, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin+i*thickness+fThicknessTyvk+fThicknessAbsorber/2.0, 0, kTRUE, buf, 0);
    if (fThicknessTyvk>0.0)
    {
      gGeoManager->Node(tyvek.Data(), 2*i+1, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin+i*thickness+1.5*fThicknessTyvk+fThicknessAbsorber, 0, kTRUE, buf, 0);
      gGeoManager->Node(tyvek.Data(), 2*i+2, nm.Data(), 0.0, 0.0, -thickness*fNLayers/2.0+fThicknessScin+i*thickness+0.5*fThicknessTyvk, 0, kTRUE, buf, 0);
    }
  }
  
  fModuleLength=moduleth;
  fModule=modulev;
}
// -------------------------------------------------------------------------

// -----   Private method InitMedium ---------------------------------------    
Int_t hcal::InitMedium(const char* name)
{
  static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
  static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
  static FairGeoMedia *media=geoFace->getMedia();
  static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

  FairGeoMedium *CbmMedium=media->getMedium(name);

  if (!CbmMedium)
  {
    Fatal("InitMedium","Material %s not defined in media file.", name);
    return -1111;
  }
  TGeoMedium* medium=gGeoManager->GetMedium(name);
  if (medium!=NULL)
    return CbmMedium->getMediumIndex();

  return geoBuild->createMedium(CbmMedium);
}
// -------------------------------------------------------------------------

// -----   Private method InitMedia ----------------------------------------    
void hcal::InitMedia()
{
  Info("InitMedia", "Initializing media.");
  InitMedium("SensVacuum");
  InitMedium("ECALVacuum");
  InitMedium(fAbsorber.Data());
  InitMedium("Scintillator");
  InitMedium("Tyvek");
  InitMedium("ECALAir");
  InitMedium("ECALFiber");
  InitMedium("ECALSteel");
  InitMedium("ECALTileEdging");
}
// -------------------------------------------------------------------------

// -----   Private method ConstructTile ------------------------------------    
void hcal::ConstructTile(Int_t material)
{
  switch (material)
  {
    case 0: if (fScTile!=NULL) return; break;
    case 1: if (fPbTile!=NULL) return; break;
    case 2: if (fTvTile!=NULL) return; break;
    default: Error("ConstructTile", "Can't construct a tile of type %d.", material);
  }
  Double_t thickness;
  TGeoVolume* hole;
  TGeoVolume* fiber;
  TGeoTranslation** tr;
  TGeoTranslation* tm;
  Int_t nh=fNH;
  Int_t i;
  Int_t j;
  TString nm;
  TString nm1;
  TString nm2;
  TString medium;
  Double_t x;
  Double_t y;
  TGeoBBox* tile;
  TGeoVolume* tilev;
  TGeoBBox* edging;
  TGeoVolume* edgingv;
  Double_t* buf=NULL;

  switch (material)
  {
    case 0: thickness=fThicknessScin/2.0; break;
    case 1: thickness=fThicknessAbsorber/2.0; break;
    case 2: thickness=fThicknessTyvk/2.0; break;
    default: Error("ConstructTile", "Can't construct a tile of type %d.", material);
  }

  if (thickness<=0.0) return;
  // Holes in the tiles
  if (fHoleRad>0)
  {
    nm1="ECALHole_"; nm1+=material;
    nm2="ECALFiber_"; nm2+=material;
    if (fHoleVol[material]==NULL)
    {
      TGeoTube* holetube=new TGeoTube(0, fHoleRad, thickness);
      fHoleVol[material]=new TGeoVolume(nm1.Data(), holetube,  gGeoManager->GetMedium("ECALAir"));
    }
    hole=fHoleVol[material];
    // Fibers in holes 
    if (fFiberRad>0)
    {
      if (fFiberVol[material]==NULL)
      {
        TGeoTube* fibertube=new TGeoTube(0, fFiberRad, thickness);
        fFiberVol[material]=new TGeoVolume(nm2.Data(), fibertube,  gGeoManager->GetMedium("ECALFiber"));
        gGeoManager->Node(nm2.Data(), 1, nm1.Data(), 0.0, 0.0, 0.0, 0, kTRUE, buf, 0);
      }
      fiber=fFiberVol[material];
      // TODO: Cerenkoff !!!
      //AddSensitiveVolume(fiber);
    }
  }
/*
  if (fHolePos==NULL)
  {
    tr=new TGeoTranslation*[nh*nh];
    for(i=0;i<nh;i++)
    for(j=0;j<nh;j++)
    {
      nm="sh"; nm+="_"; nm+=j*nh+i;
      x=(i-nh/2+0.5)*fXCell/nh;
      y=(j-nh/2+0.5)*fYCell/nh;


      tm=new TGeoTranslation(nm, x, y, 0);
      gGeoManager->AddTransformation(tm);
      tr[j*nh+i]=tm;
    }
    fHolePos=tr;
  }
  tr=fHolePos;
*/
  /** Building tile **/
  switch (material)
  {
    case 0: nm="ScTile"; medium="Scintillator"; break;
    case 1: nm="LeadTile"; medium=fAbsorber; break;
    case 2: nm="TvTile"; medium="Tyvek"; break;
    default: Error("ConstructTile", "Can't construct a tile of type %d.", material);
  }

  if (material==0)
    tile=new TGeoBBox(fXCell/2.0, fYCell/2.0, thickness);
  else
    tile=new TGeoBBox(fXCell/2.0+fEdging, fYCell/2.0+fEdging, thickness);
  tilev=new TGeoVolume(nm, tile, gGeoManager->GetMedium(medium));
  if (fHoleRad>0)
  {
    nm1="ECALHole_"; nm1+=material;
    for(i=0;i<nh;i++)
    for(j=0;j<nh;j++)
    {
      x=(i-nh/2+0.5)*fXCell/nh;
      y=(j-nh/2+0.5)*fYCell/nh;
      gGeoManager->Node(nm1.Data(), j*nh+i+1, nm.Data(), x, y, 0.0, 0, kTRUE, buf, 0);
    }
    // clear fiber
    if (nh%2==0&&fCF!=0)
      gGeoManager->Node(nm1.Data(), j*nh+i+1, nm.Data(), 0.0, 0.0, 0.0, 0, kTRUE, buf, 0);

  }
/*
  if (fHoleRad>0)
  {
    for(i=0;i<nh;i++)
    for(j=0;j<nh;j++)
      tilev->AddNode(hole, j*nh+i+1, tr[j*nh+i]);
    // Clear Fiber
    if (nh%2==0)
      tilev->AddNode(hole, j*nh+i+1);
  }
*/
  /** Adding edging to scintillator **/
  if (material==0)
  {
    AddSensitiveVolume(tilev);
    edging=new TGeoBBox(fXCell/2.0+fEdging, fYCell/2.0+fEdging, thickness);
     
    edgingv=new TGeoVolume(nm+"_edging", edging, gGeoManager->GetMedium("ECALTileEdging"));
    edgingv->AddNode(tilev, 1);
    fScTile=tilev;
    fTileEdging=edgingv;
  }
  else
  {
    if (material==1) //Lead
      fPbTile=tilev;
    else
      fTvTile=tilev;
    return;
  }
}
// -------------------------------------------------------------------------

// -----   Private method ConstructTileSimple ------------------------------    
void hcal::ConstructTileSimple(Int_t material)
{
  switch (material)
  {
    case 0: if (fScTile!=NULL) return; break;
    case 1: if (fPbTile!=NULL) return; break;
    case 2: if (fTvTile!=NULL) return; break;
    default: Error("ConstructTileSimple", "Can't construct a tile of type %d.", material);
  }
  Double_t thickness;
  TGeoVolume* hole;
  TGeoVolume* fiber;
  TGeoTranslation** tr;
  TGeoTranslation* tm;
  Int_t nh=fNH;
  Int_t i;
  Int_t j;
  TString nm;
  TString nm1;
  TString nm2;
  TString medium;
  Double_t x;
  Double_t y;
  TGeoBBox* tile;
  TGeoVolume* tilev;
  TGeoBBox* edging;
  TGeoVolume* edgingv;
  Double_t* buf=NULL;

  switch (material)
  {
    case 0: thickness=fThicknessScin/2.0; break;
    case 1: thickness=fThicknessAbsorber/2.0; break;
    case 2: thickness=fThicknessTyvk/2.0; break;
    default: Error("ConstructTile", "Can't construct a tile of type %d.", material);
  }

  if (thickness<=0.0) return;
  /** Building tile **/
  switch (material)
  {
    case 0: nm="ScTile"; medium="Scintillator"; break;
    case 1: nm="LeadTile"; medium=fAbsorber; break;
    case 2: nm="TvTile"; medium="Tyvek"; break;
    default: Error("ConstructTile", "Can't construct a tile of type %d.", material);
  }

  tile=new TGeoBBox(fModuleSize/2.0, fModuleSize/2.0, thickness);
  tilev=new TGeoVolume(nm, tile, gGeoManager->GetMedium(medium));
  /** Adding edging to scintillator **/
  if (material==0)
  {
    AddSensitiveVolume(tilev);
    fScTile=tilev;
    fTileEdging=tilev;
  }
  else
  {
    if (material==1) //Absorber
      fPbTile=tilev;
    else
      fTvTile=tilev;
    return;
  }
}
// -------------------------------------------------------------------------

// ----- Public method GetCellCoordInf ----------------------------------------
Bool_t hcal::GetCellCoordInf(Int_t fVolID, Float_t &x, Float_t &y, Int_t& section)
{
  static hcalInf* inf=NULL;
  if (inf==NULL)
  {
    inf=hcalInf::GetInstance(NULL);
    if (inf==NULL)
    {
      cerr << "hcal::GetCellCoordInf(): Can't get geometry information." << endl;
      return kFALSE;
    }
  }
  Int_t volid=fVolID;
  section=volid%10; volid=volid-section; volid/=10;
  Int_t mx=volid%100; volid-=mx; volid/=100;
  Int_t my=volid%100; volid-=my; volid/=100;
  static Float_t modulesize=inf->GetVariableStrict("modulesize");
  static Float_t xcalosize=inf->GetHcalSize(0);
  static Float_t ycalosize=inf->GetHcalSize(1);
  static Float_t dx=inf->GetVariableStrict("xpos");
  static Float_t dy=inf->GetVariableStrict("ypos");
  x=mx*modulesize-xcalosize/2.0+1.0; x+=dx;
  y=my*modulesize-ycalosize/2.0+1.0; y+=dy;

  return kFALSE;
}

// ------------------------------------------------------------------------------

Bool_t hcal::GetCellCoord(Int_t fVolID, Float_t &x, Float_t &y, Int_t& section)
{
  return GetCellCoordInf(fVolID, x, y, section);
}


