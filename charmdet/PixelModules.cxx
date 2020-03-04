// PixelModules.cxx
//  PixelModules, twelve pixel modules physically connected two by two.

#include "PixelModules.h"
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
   : FairDetector("HighPrecisionTrackers", kTRUE, kPixelModules), fTrackID(-1), fPdgCode(), fVolumeID(-1), fPos(),
     fMom(), fTime(-1.), fLength(-1.), fELoss(-1), fPixelModulesPointCollection(new TClonesArray("PixelModulesPoint"))
{
}

PixelModules::PixelModules(const char *name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,
                           Int_t nSl, const char *Title)
   : FairDetector(name, Active, kPixelModules), fTrackID(-1), fPdgCode(), fVolumeID(-1), fPos(), fMom(), fTime(-1.),
     fLength(-1.), fELoss(-1), fPixelModulesPointCollection(new TClonesArray("PixelModulesPoint"))
{
   DimX = DX;
   DimY = DY;
   DimZ = DZ;
   DimZWindow = 0.0110 * cm;
   Windowx = 5 * cm;
   Windowy = 5 * cm;
   FrontEndthick = 0.0150 * cm;
   FlexCuthick = 0.0100 * cm;
   FlexKapthick = 0.0050 * cm;
   SetSiliconSlicesNumber(nSl);
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



void PixelModules::SetSiliconDZ(Double_t SiliconDZthin,Double_t SiliconDZthick)
{
  DimZSithin = SiliconDZthin;
  DimZSithick= SiliconDZthick;
}

void PixelModules::SetSiliconSlicesNumber(Int_t nSl)
{
   nSlices = nSl;
   nSi = nSlices * 12;
}

void PixelModules::SetPositionSize()
{
   xs = std::vector<Double_t> (nSi);
   ys = std::vector<Double_t> (nSi);
   zs = std::vector<Double_t> (nSi);

   xangle = std::vector<Double_t> (nSi);
   yangle = std::vector<Double_t> (nSi);
   zangle = std::vector<Double_t> (nSi);
}

void PixelModules::SetSiliconStationPositions(Int_t nstation, Double_t posx, Double_t posy, Double_t posz)
{
   xs[nstation] = posx;
   ys[nstation] = posy;
   zs[nstation] = posz;
}

void PixelModules::SetSiliconStationAngles(Int_t nstation, Double_t anglex, Double_t angley, Double_t anglez){
 xangle[nstation] = anglex;
 yangle[nstation] = angley;
 zangle[nstation] = anglez;
}

void PixelModules::ComputeDimZSlice()
{
   DimZThinSlice = DimZSithin / nSlices;
   DimZThickSlice = DimZSithick / nSlices;
}

void PixelModules::SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox, Double_t SZPixel, Double_t D1short,
                               Double_t D1long, Double_t SiliconDZthin, Double_t SiliconDZthick, Double_t first_plane_offset)
{
   SBoxX = SX;
   SBoxY = SY;
   SBoxZ = SZ;
   zBoxPosition = zBox;
   DimZPixelBox = SZPixel;
   Dim1Short = D1short;
   Dim1Long = D1long;
   z_offset = first_plane_offset; // distance between first module and box outside
   SetSiliconDZ(SiliconDZthin, SiliconDZthick);
   ComputeDimZSlice();
   SetIDs();
   SetPositionSize();
}

void PixelModules::SetIDs()
{
   for (Int_t i = 0; i < nSi; i++) {
      PixelIDlist.push_back(i);
   }
}

void PixelModules::ConstructGeometry()
{

    InitMedium("iron");
    TGeoMedium *Fe =gGeoManager->GetMedium("iron");

    InitMedium("silicon");
    TGeoMedium *Silicon = gGeoManager->GetMedium("silicon");

   InitMedium("aluminium");
   TGeoMedium *Aluminium = gGeoManager->GetMedium("aluminium");

   InitMedium("copper");
   TGeoMedium *Copper = gGeoManager->GetMedium("copper");

   InitMedium("kapton");
   TGeoMedium *Kapton = gGeoManager->GetMedium("kapton");

   InitMedium("CoilCopper");
   TGeoMedium *Cu = gGeoManager->GetMedium("CoilCopper");

   InitMedium("CoilAluminium");
   TGeoMedium *Al = gGeoManager->GetMedium("CoilAluminium");

   InitMedium("TTmedium");
   TGeoMedium *TT = gGeoManager->GetMedium("TTmedium");

   InitMedium("STTmix8020_2bar");
   TGeoMedium *sttmix8020_2bar = gGeoManager->GetMedium("STTmix8020_2bar");

   TGeoVolume *top = gGeoManager->GetTopVolume();

   TGeoVolumeAssembly *volPixelBox = new TGeoVolumeAssembly("volPixelBox");
   top->AddNode(volPixelBox, 1, new TGeoTranslation(0, 0, zBoxPosition ));

   // TGeoBBox *Pixelythin = new TGeoBBox("Pixelythin", Dim1Short / 2, Dim1Long / 2, DimZThinSlice / 2); // long along y
   // TGeoVolume *volPixelythin = new TGeoVolume("volPixelythin", Pixelythin, Silicon);
   // volPixelythin->SetLineColor(kBlue - 5);
   // AddSensitiveVolume(volPixelythin);

   TGeoBBox *Pixelxthin = new TGeoBBox("Pixelxthin", (Dim1Long) / 2, (Dim1Short) / 2, DimZThinSlice / 2); // long along
                                                                                                          // x
   TGeoVolume *volPixelxthin = new TGeoVolume("volPixelxthin", Pixelxthin, Silicon);
   volPixelxthin->SetLineColor(kBlue - 5);
   AddSensitiveVolume(volPixelxthin);

   TGeoBBox *Pixelythick = new TGeoBBox("Pixelythick", Dim1Short / 2, Dim1Long / 2, DimZThickSlice / 2.); // long along y
   TGeoVolume *volPixelythick = new TGeoVolume("volPixelythick", Pixelythick, Silicon);
   volPixelythick->SetLineColor(kBlue - 5);
   AddSensitiveVolume(volPixelythick);

   TGeoBBox *Pixelxthick =
      new TGeoBBox("Pixelxthick", (Dim1Long) / 2, (Dim1Short) / 2, DimZThickSlice / 2.); // long along x
   TGeoVolume *volPixelxthick = new TGeoVolume("volPixelxthick", Pixelxthick, Silicon);
   volPixelxthick->SetLineColor(kBlue - 5);
   AddSensitiveVolume(volPixelxthick);

   //////////////////////Passive material//////////////////////

   TGeoBBox *WindowBox = new TGeoBBox("WindowBox", Windowx / 2, Windowy / 2, DimZWindow / 2);
   TGeoVolume *volWindow = new TGeoVolume("volWindow", WindowBox, Kapton);
   volWindow->SetLineColor(kRed);

   TGeoBBox *FrontEndx = new TGeoBBox("FrontEndx", Dim1Long / 2, Dim1Short / 2, FrontEndthick / 2);
   TGeoVolume *volFrontEndx = new TGeoVolume("volFrontEndx", FrontEndx, Silicon);
   volFrontEndx->SetLineColor(kRed);

   TGeoBBox *FrontEndy = new TGeoBBox("FrontEndy", Dim1Short / 2, Dim1Long / 2, FrontEndthick / 2);
   TGeoVolume *volFrontEndy = new TGeoVolume("volFrontEndy", FrontEndy, Silicon);
   volFrontEndy->SetLineColor(kRed);

   TGeoBBox *FlexCux = new TGeoBBox("FlexCux", Dim1Long / 2, Dim1Short / 2, FlexCuthick / 2);
   TGeoVolume *volFlexCux = new TGeoVolume("volFlexCux", FlexCux, Copper);
   volFlexCux->SetLineColor(kRed);

   TGeoBBox *FlexCuy = new TGeoBBox("FlexCuy", Dim1Short / 2, Dim1Long / 2, FlexCuthick / 2);
   TGeoVolume *volFlexCuy = new TGeoVolume("volFlexCuy", FlexCuy, Copper);
   volFlexCuy->SetLineColor(kRed);

   TGeoBBox *FlexKapx = new TGeoBBox("FlexKapx", Dim1Long / 2, Dim1Short / 2, FlexKapthick / 2);
   TGeoVolume *volFlexKapx = new TGeoVolume("volFlexKapx", FlexKapx, Kapton);
   volFlexKapx->SetLineColor(kRed);

   TGeoBBox *FlexKapy = new TGeoBBox("FlexKapy", Dim1Short / 2, Dim1Long / 2, FlexKapthick / 2);
   TGeoVolume *volFlexKapy = new TGeoVolume("volFlexKapy", FlexKapy, Kapton);
   volFlexKapy->SetLineColor(kRed);

   //////////////////////End Passive material//////////////////////

   // place foil which covered the entry window of the pixelbox.
   volPixelBox->AddNode(volWindow, 0, new TGeoTranslation(0, 0, -DimZPixelBox / 2. + DimZWindow));
   volPixelBox->AddNode(volWindow, 1, new TGeoTranslation(0, 0, DimZPixelBox / 2. - DimZWindow));
   
   // loop to create and align the active volumes ( == Sensors). Only the active material is sliced.
   for (Int_t ipixel = 0; ipixel < nSi; ipixel++) {
       // modules with large pixel pitch in y
      if ((ipixel / nSlices) % 4 == 0 || (ipixel / nSlices) % 4 == 1) {
         volPixelBox->AddNode(volPixelythick, PixelIDlist[ipixel],
            new TGeoTranslation(xs[ipixel], ys[ipixel], (-DimZPixelBox / 2.) + zs[ipixel] + z_offset));
      } else { // modules with large pixel pitch in x
         // consider the two thinner modules
         if (((PixelIDlist[ipixel] / nSlices) == 2) || ((PixelIDlist[ipixel] / nSlices) == 11)) { 
            volPixelBox->AddNode(volPixelxthin, PixelIDlist[ipixel],
               new TGeoTranslation(xs[ipixel], ys[ipixel], (-DimZPixelBox / 2.) + zs[ipixel] + z_offset));
         } else {
            volPixelBox->AddNode(volPixelxthick, PixelIDlist[ipixel],
               new TGeoTranslation(xs[ipixel], ys[ipixel], (-DimZPixelBox / 2.) + zs[ipixel] + z_offset));
         }
      }
   }

   // put passive materials in place (flex and FE)
   Double_t z_tmp_cu = 0. ;
   Double_t z_tmp_fe = 0. ;
   Double_t z_tmp_kap = 0. ;
   for (Int_t module = 0; module < nSi; module += nSlices) {
      if ((module) % 4 == 0 || (module) % 4 == 1) {
         // modules with large pixel pitch in y
         if ((module) % 4 == 0) {
            // flex is upstream, FE is downstream of sensor
            z_tmp_cu = (-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThickSlice / 2.) - FlexKapthick - (FlexCuthick/ 2.) ;
            z_tmp_kap =(-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThickSlice / 2.) - FlexKapthick / 2. ;
            z_tmp_fe = (-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThickSlice / 2.) + (FrontEndthick/ 2.) ;
         } else {
            // FE is upstream, flex is downstream of sensor
            z_tmp_fe = (-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThickSlice / 2.) - (FrontEndthick/ 2.) ;
            z_tmp_kap =(-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThickSlice / 2.) + FlexKapthick / 2. ;
            z_tmp_cu = (-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThickSlice / 2.) + FlexKapthick / 2. + (FlexCuthick/ 2.)  ;
         }
         volPixelBox->AddNode(volFrontEndy, module, new TGeoTranslation(xs[module], ys[module], z_tmp_fe));
         volPixelBox->AddNode(volFlexCuy, module, new TGeoTranslation(xs[module], ys[module], z_tmp_cu));
         volPixelBox->AddNode(volFlexKapy, module, new TGeoTranslation(xs[module], ys[module], z_tmp_kap));
      } else {
         // modules with large pixel pitch in x
         // consider thinner modules
         if (module == 2 ){
            z_tmp_cu = (-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThinSlice / 2.) - FlexKapthick - (FlexCuthick/ 2.) ;
            z_tmp_kap =(-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThinSlice / 2.) - FlexKapthick / 2. ;
            z_tmp_fe = (-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThinSlice / 2.) + (FrontEndthick/ 2.) ;
         }
         else if (module == 11){
            z_tmp_fe = (-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThinSlice / 2.) - (FrontEndthick/ 2.) ;
            z_tmp_kap =(-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThinSlice / 2.) + FlexKapthick / 2. ;
            z_tmp_cu = (-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThinSlice / 2.) + FlexKapthick / 2. + (FlexCuthick/ 2.)  ;
         }
         else if ((module) % 4 == 2) {
            // flex is upstream, FE is downstream of sensor
            z_tmp_cu = (-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThickSlice / 2.) - FlexKapthick - (FlexCuthick/ 2.) ;
            z_tmp_kap =(-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThickSlice / 2.) - FlexKapthick / 2. ;
            z_tmp_fe = (-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThickSlice / 2.) + (FrontEndthick/ 2.) ;
         } else if (module % 4 == 3){
            // FE is upstream, flex is downstream of sensor
            z_tmp_fe = (-DimZPixelBox / 2.) + zs[module] + z_offset - (DimZThickSlice / 2.) - (FrontEndthick/ 2.) ;
            z_tmp_kap =(-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThickSlice / 2.) + FlexKapthick / 2. ;
            z_tmp_cu = (-DimZPixelBox / 2.) + zs[module + nSlices - 1] + z_offset + (DimZThickSlice / 2.) + FlexKapthick / 2. + (FlexCuthick/ 2.)  ;
         }
         volPixelBox->AddNode(volFrontEndx, module, new TGeoTranslation(xs[module], ys[module], z_tmp_fe));
         volPixelBox->AddNode(volFlexCux, module, new TGeoTranslation(xs[module], ys[module], z_tmp_cu));
         volPixelBox->AddNode(volFlexKapx, module, new TGeoTranslation(xs[module], ys[module], z_tmp_kap));
      }
   }
}

Bool_t  PixelModules::ProcessHits(FairVolume* vol){
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
                        Double_t time, Double_t length, Double_t eLoss, Int_t pdgCode)

{
    TClonesArray& clref = *fPixelModulesPointCollection;
    Int_t size = clref.GetEntriesFast();

    return new(clref[size]) PixelModulesPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode);
}


ClassImp(PixelModules)
