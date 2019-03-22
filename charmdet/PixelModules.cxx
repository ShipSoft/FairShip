// PixelModules.cxx
//  PixelModules, twelve pixel modules physically connected two by two.

#include "PixelModules.h"
//#include "MagneticPixelModules.h"
#include "PixelModulesPoint.h"
#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TClonesArray.h"
#include "TVirtualMC.h"

#include "TGeoBBox.h"
#include "TGeoTrd1.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoArb8.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TParticle.h"
#include "TVector3.h"

#include "FairVolume.h"
#include "FairGeoVolume.h"
#include "FairGeoNode.h"
#include "FairRootManager.h"
#include "FairGeoLoader.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"

#include "ShipDetectorList.h"
#include "ShipUnit.h"
#include "ShipStack.h"

#include "TGeoUniformMagField.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using std::cout;
using std::endl;
using namespace ShipUnit;

PixelModules::PixelModules()
  : FairDetector("HighPrecisionTrackers",kTRUE, kPixelModules),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fPixelModulesPointCollection(new TClonesArray("PixelModulesPoint"))
{
}

PixelModules::PixelModules(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,const char* Title)
  : FairDetector(name, Active, kPixelModules),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fPixelModulesPointCollection(new TClonesArray("PixelModulesPoint"))
{
  DimX = DX;
  DimY = DY;
  DimZ = DZ;
}

PixelModules::~PixelModules()
{
    if (fPixelModulesPointCollection) {
        fPixelModulesPointCollection->Delete();
        delete fPixelModulesPointCollection;
    }
}

void PixelModules::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t PixelModules::InitMedium(const char* name)
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium(name);

   if (!ShipMedium)
   {
     Fatal("InitMedium","Material %s not defined in media file.", name);
     return -1111;
   }
   TGeoMedium* medium=gGeoManager->GetMedium(name);
   if (medium!=NULL)
     return ShipMedium->getMediumIndex();
   return geoBuild->createMedium(ShipMedium);
}

void PixelModules::SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox, Double_t SZPixel, Double_t D1short, Double_t D1long)
{
  SBoxX = SX;
  SBoxY = SY;
  SBoxZ = SZ;
  zBoxPosition = zBox;
  DimZPixelBox = SZPixel;
  Dim1Short = D1short;
  Dim1Long = D1long;
}

void PixelModules::SetSiliconDZ(Double_t SiliconDZ)
{
  DimZSi = SiliconDZ;
}


void PixelModules::SetSiliconStationPositions(Int_t nstation, Double_t posx, Double_t posy, Double_t posz)
{
 xs[nstation] = posx;
 ys[nstation] = posy;
 zs[nstation] = posz;
}

void PixelModules::SetSiliconStationAngles(Int_t nstation, Double_t anglex, Double_t angley, Double_t anglez)
{
 xangle[nstation] = anglex;
 yangle[nstation] = angley;
 zangle[nstation] = anglez;
}

void PixelModules::SetSiliconDetNumber(Int_t nSilicon)
{
 nSi = nSilicon;
}


std::unordered_map<int, TVector3> * PixelModules::MakePositionMap() {
// map unique detectorID to x,y,z position in LOCAL coordinate system. xy (0,0) is on the bottom left of each Front End,
// the raw data counts columns from 1-80 from left to right and rows from 1-336 FROM TOP TO BOTTOM.

  const float mkm = 0.0001;

  const float  z0ref=  -1300.*mkm;
  const float  z1ref=   5200.*mkm;
  const float  z2ref=  24120.*mkm;
  const float  z3ref=  30900.*mkm;
  const float  z4ref=  51000.*mkm;
  const float  z5ref=  57900.*mkm;
  const float  z6ref=  77900.*mkm;
  const float  z7ref=  84600.*mkm;
  const float  z8ref= 104620.*mkm;
  const float  z9ref= 111700.*mkm;
  const float z10ref= 131620.*mkm;
  const float z11ref= 138500.*mkm;

  const float Zref[12]={z0ref, z1ref, z2ref, z3ref, z4ref, z5ref, z6ref, z7ref, z8ref, z9ref, z10ref, z11ref};

  const float  x0ref= 15396.*mkm      +z0ref/mkm*0.0031;
  const float  x1ref= -2310.*mkm       +z1ref/mkm*0.0031;
  const float  x2ref=  6960.*mkm       +z2ref/mkm*0.0031;
  const float  x3ref=  6940.*mkm       +z3ref/mkm*0.0031;
  const float  x4ref= 15285.*mkm       +z4ref/mkm*0.0031;
  const float  x5ref= -2430.*mkm       +z5ref/mkm*0.0031;
  const float  x6ref=  6620.*mkm       +z6ref/mkm*0.0031;
  const float  x7ref=  6710.*mkm       +z7ref/mkm*0.0031;
  const float  x8ref= 15440.*mkm       +z8ref/mkm*0.0031;
  const float  x9ref= -2505.*mkm       +z9ref/mkm*0.0031;
  const float x10ref=  6455.*mkm      +z10ref/mkm*0.0031;
  const float x11ref=  6320.*mkm      +z11ref/mkm*0.0031;

  const float Xref[12] { x0ref, x1ref, x2ref, x3ref, x4ref, x5ref, x6ref, x7ref, x8ref, x9ref, x10ref, x11ref};

  const float  y0ref=   -15.*mkm       +z0ref*0.0068;
  const float  y1ref=    20.*mkm       +z1ref*0.0068;
  const float  y2ref=  7930.*mkm       +z2ref*0.0068;
  const float  y3ref= -8990.*mkm       +z3ref*0.0068;
  const float  y4ref=  -370.*mkm       +z4ref*0.0068;
  const float  y5ref=  -610.*mkm       +z5ref*0.0068;
  const float  y6ref=  7200.*mkm       +z6ref*0.0068;
  const float  y7ref= -9285.*mkm       +z7ref*0.0068;
  const float  y8ref=  -700.*mkm       +z8ref*0.0068;
  const float  y9ref=  -690.*mkm       +z9ref*0.0068;
  const float y10ref=  7660.*mkm       +z10ref*0.0068;
  const float y11ref= -8850.*mkm      +z11ref*0.0068;

  const float Yref[12] { y0ref, y1ref, y2ref, y3ref, y4ref, y5ref, y6ref, y7ref, y8ref, y9ref, y10ref, y11ref};

  std::unordered_map<int, TVector3> positionMap;
  std::vector<std::vector<TVector3>> alignment(12);

  for (int i=0; i<12; i++) {
    (*alignment[i]).SetX(Xref[i]);
    (*alignment[i]).SetX(Yref[i]);
    (*alignment[i]).SetZ(Zref[i]);
  }

  int map_index = 0;
  int moduleID = 0;
  float x,x_lcoal,y, y_local;
  for (int partID=0; partID<3; partID++) {
    for (int frontEndID=0;frontEndID<8; frontEndID++ ) {
      for (int column=1; column<81; column++) {
        for (int row=1; row<337; row++) {
          map_index = 10000000*partID + 1000000*frontEndID + 1000*row + column;
          moduleID = (8*partitionID + frontEndID)/2;
          if (frontEndID%2==1) {
            // calculate LOCAL x position of hit
            x_local = -0.025 - (column-1)*0.025;
            if (column == 80) x_local -= 0.0225;
          }
          else if (frontEndID%2==0) {
            x_local = 0.0225 + (column-1)*0.025;
            if (column == 80) x_local += 0.025;
          }
          // calculate LOCAL y position of hit
          y_local = 1.6775 - 0.0050*(row-1);
          // transform local to global coordinates
          if (frontEndID == 0){
            x = -y_local;
            y = x_local;
          }
          if (frontEndID == 1 ){
            x = -y_local;
            y = x_local;
          }
          if (frontEndID == 2 ){
            x = y_local;
            y = x_local;
          }
          if (frontEndID == 3 ) {
            x = y_local;
            y = x_local;
          }
          if (frontEndID == 4 ){
            x = -x_local;
            y = -y_local;
          }
          if (frontEndID == 5 ){
            x = -x_local;
            y = -y_local;
          }
          if (frontEndID == 6 ){
            x = -x_local;
            y = y_local;
          }
          if (frontEndID == 7 ){
            x = -x_local;
            y = y_local;
          }
          positionMap[map_index].SetX(x - Xref[moduleID]);
          positionMap[map_index].SetY(y - Yref[moduleID]);
          positionMap[map_index].SetZ(Zref[moduleID]);
        }
      }
    }
  }
return &positionMap;
}


void PixelModules::ConstructGeometry()
{
    InitMedium("air");
  TGeoMedium *air = gGeoManager->GetMedium("air");

    InitMedium("iron");
    TGeoMedium *Fe =gGeoManager->GetMedium("iron");

    InitMedium("silicon");
    TGeoMedium *Silicon = gGeoManager->GetMedium("silicon");

    InitMedium("CoilCopper");
    TGeoMedium *Cu  = gGeoManager->GetMedium("CoilCopper");

    InitMedium("CoilAluminium");
    TGeoMedium *Al  = gGeoManager->GetMedium("CoilAluminium");

    InitMedium("TTmedium");
    TGeoMedium *TT  = gGeoManager->GetMedium("TTmedium");

    InitMedium("STTmix8020_2bar");
    TGeoMedium *sttmix8020_2bar   = gGeoManager->GetMedium("STTmix8020_2bar");

    TGeoVolume *top = gGeoManager->GetTopVolume();

    //computing the largest offsets in order to set PixelBox dimensions correctly
    Double_t offsetxmax = 0., offsetymax = 0.;
    for (int istation = 0; istation < 12; istation++){
     if (TMath::Abs(xs[istation]) > offsetxmax) offsetxmax = TMath::Abs(xs[istation]);
     if (TMath::Abs(ys[istation]) > offsetymax) offsetymax = TMath::Abs(ys[istation]);
    }
    //Double_t DimZPixelBox = zs5 -zs0 +pairwisedistance + DimZSi;
    TGeoBBox *PixelBox = new TGeoBBox("PixelBox", Dim1Long/2 + offsetxmax, Dim1Long/2 + offsetymax, DimZPixelBox/2.); //The box is symmetric, offsets are not. So we enlarge the offset by a factor two for coverage
    TGeoVolume *volPixelBox = new TGeoVolume("volPixelBox",PixelBox,air);
    Double_t inimodZoffset(zs[0]) ;//initial Z offset of Pixel Module 0 so as to avoid volume extrusion
    top->AddNode(volPixelBox, 1, new TGeoTranslation(0,0,zBoxPosition+ inimodZoffset)); //volume moved in


    TGeoBBox *Pixely = new TGeoBBox("Pixely", Dim1Short/2, Dim1Long/2, DimZSi/2); //long along y
    TGeoVolume *volPixely = new TGeoVolume("volPixely",Pixely,Silicon);
    volPixely->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixely);

    TGeoBBox *Pixelx = new TGeoBBox("Pixelx", (Dim1Long)/2, (Dim1Short)/2, DimZSi/2); //long along x
    TGeoVolume *volPixelx = new TGeoVolume("volPixelx",Pixelx,Silicon);
    volPixelx->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixelx);

    //id convention: 1{a}{b}, a = number of pair (from 1 to 6), b = element of the pair (1 or 2)
    Int_t PixelIDlist[12] = {111,112,121,122,131,132,141,142,151,152,161,162};
    //Alternated pixel stations optimized for y and x measurements
    Bool_t vertical[12] = {kTRUE,kTRUE,kFALSE,kFALSE,kTRUE,kTRUE,kFALSE,kFALSE,kTRUE,kTRUE,kFALSE,kFALSE};

    for (int ipixel = 0; ipixel < 12; ipixel++){
      if (vertical[ipixel]) volPixelBox->AddNode(volPixely, PixelIDlist[ipixel], new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset)); //compensation for the Node offset
      else volPixelBox->AddNode(volPixelx, PixelIDlist[ipixel], new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset));
    }

}

Bool_t  PixelModules::ProcessHits(FairVolume* vol)
{
    /** This method is called from the MC stepping */
    //Set parameters at entrance of volume. Reset ELoss.
    if ( gMC->IsTrackEntering() ) {
        fELoss  = 0.;
        fTime   = gMC->TrackTime() * 1.0e09;
        fLength = gMC->TrackLength();
        gMC->TrackPosition(fPos);
        gMC->TrackMomentum(fMom);
    }
    // Sum energy loss for all steps in the active volume
    fELoss += gMC->Edep();

    // Create muonPoint at exit of active volume
    if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       ||
        gMC->IsTrackDisappeared()   ) {
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();

        if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();
	//Int_t fMotherID =p->GetFirstMother();
        gMC->CurrentVolID(fVolumeID);

        TLorentzVector Pos;
        gMC->TrackPosition(Pos);
        Double_t xmean = (fPos.X()+Pos.X())/2. ;
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;

	AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean), TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,fELoss, pdgCode);

        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(kPixelModules);
    }

    return kTRUE;
}

void PixelModules::EndOfEvent()
{
    fPixelModulesPointCollection->Clear();
}


void PixelModules::Register()
{

    /** This will create a branch in the output tree called
     PixelModulesPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */

    FairRootManager::Instance()->Register("PixelModulesPoint", "PixelModules",
                                          fPixelModulesPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------
// -----   returns hpt, arm, rpc numbers -----------------------------------
void PixelModules::DecodeVolumeID(Int_t detID,int &nHPT)
{
  nHPT = detID;
}

TClonesArray* PixelModules::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fPixelModulesPointCollection; }
    else { return NULL; }
}

void PixelModules::Reset()
{
    fPixelModulesPointCollection->Clear();
}


PixelModulesPoint* PixelModules::AddHit(Int_t trackID, Int_t detID,
                        TVector3 pos, TVector3 mom,
                        Double_t time, Double_t length,
					    Double_t eLoss, Int_t pdgCode)

{
    TClonesArray& clref = *fPixelModulesPointCollection;
    Int_t size = clref.GetEntriesFast();

    return new(clref[size]) PixelModulesPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode);
}


ClassImp(PixelModules)
