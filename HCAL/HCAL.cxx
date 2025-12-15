// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#include "HCAL.h"

#include "HCALPoint.h"


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
#include "ShipStack.h"

#include "TClonesArray.h"
#include "TVirtualMC.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoShapeAssembly.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TParticle.h"

#include "TROOT.h"
#include "TCanvas.h"
#include "TView3D.h"


#include <RtypesCore.h>
#include <iostream>
using std::cout;
using std::endl;

HCAL::HCAL()
  : FairDetector("HCAL", kTRUE, kHCAL),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fHCALPointCollection(new TClonesArray("HCALPoint"))
{
}

HCAL::HCAL(const char* name, Bool_t active)
  : FairDetector(name, active, kHCAL),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fHCALPointCollection(new TClonesArray("HCALPoint"))
{
}

HCAL::~HCAL()
{
  if (fHCALPointCollection) {
    fHCALPointCollection->Delete();
    delete fHCALPointCollection;
  }
}

void HCAL::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  HCALGeoPar* par=(HCALGeoPar*)(rtdb->getContainer("HCALGeoPar"));
}
// -----   Private method InitMedium
Int_t HCAL::InitMedium(const char* name)
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

Bool_t  HCAL::ProcessHits(FairVolume* vol)
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

  // Create HCALPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    //fVolumeID = vol->getMCid();
    //cout << "HCAL proc "<< fVolumeID<<" "<<vol->GetName()<<" "<<vol->getVolumeId() <<endl;
    //   cout << " "<< gGeoManager->FindVolumeFast(vol->GetName())->GetNumber()<< "  " << gMC->CurrentVolID() << endl;
    ///  fVolumeID = gGeoManager->FindVolumeFast(vol->GetName())->GetNumber();
    //VolumeID = vol->getMCid();
    Int_t detID=0;
    gMC->CurrentVolID(detID);

    //if (fVolumeID == detID) {
    //  return kTRUE; }
    fVolumeID = detID;
    //    cout << " "<<fVolumeID << endl;
    if (fELoss == 0. ) { return kFALSE; }
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    //    if(fVolumeID<405 && fTime<70){
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode);

    // Increment number of HCAL det points in TParticle
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kHCAL);

  }

  return kTRUE;
}

void HCAL::EndOfEvent()
{

  fHCALPointCollection->Clear();

}



void HCAL::Register()
{

  /** This will create a branch in the output tree called
      HCALPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("HCALPoint", "HCAL",
                                        fHCALPointCollection, kTRUE);

}


TClonesArray* HCAL::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fHCALPointCollection; }
  else { return NULL; }
}

void HCAL::Reset()
{
  fHCALPointCollection->Clear();
}

void HCAL::SetNmodulesXY(Int_t NmodulesX, Int_t NmodulesY){
	fNmodulesX = static_cast<UShort_t>(NmodulesX);
	fNmodulesY = static_cast<UShort_t>(NmodulesY);
}

void HCAL::SetModuleSize(Double_t Module_size_X,Double_t Module_size_Y){
	fModule_Size_X = Module_size_X;
	fModule_Size_Y = Module_size_Y;
}

void HCAL::SetZStart(Double_t ZStart)
{
  fZStart=ZStart;
}

void HCAL::SetMaterial(Bool_t ActiveHCALMaterial)
{
    fActiveHCALMaterial = ActiveHCALMaterial;
}

void HCAL::SetNSamplings(Int_t nSamplings)
{
  fnSamplings=static_cast<UShort_t>(nSamplings);
}

void HCAL::SetNBars(Int_t nBars)
{
  fNBarsPerLayer = static_cast<UInt_t>(nBars);
}

void HCAL::SetBarSize(Double_t ScintBarSizeX, Double_t ScintBarSizeY, Double_t ScintBarSizeZ)
{
  fScintBarX = ScintBarSizeX;
  fScintBarY = ScintBarSizeY;
  fScintBarZ = ScintBarSizeZ;
}

void HCAL::SetPassiveLayerXYZ(Double_t PassiveLayerX,Double_t PassiveLayerY, Double_t PassiveLayerZ){
  fPassiveLayerX=PassiveLayerX;
  fPassiveLayerY=PassiveLayerY;
  fPassiveLayerZ=PassiveLayerZ;
}

void HCAL::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */

    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoVolume *tHCAL = new TGeoVolumeAssembly("HCALDetector");

    InitMedium("iron");
    InitMedium("Scintillator");

    TGeoMedium *passive_material =gGeoManager->GetMedium("iron");
    TGeoMedium *active_material =gGeoManager->GetMedium("Scintillator");

    Double_t zStartHCAL = fZStart;

    TGeoVolume *passive_plate;
    TGeoVolume *horibar;
    TGeoVolume *vertbar;


    //Define absorber layers 

    passive_plate = gGeoManager->MakeBox("passive_plate", passive_material, fModule_Size_X/2., fModule_Size_Y/2., fPassiveLayerZ/2.);
    passive_plate->SetLineColor(kGray);

    //Define sensitive bars
    horibar = gGeoManager->MakeBox("horibar", active_material, fScintBarX/2., fScintBarY/2., fScintBarZ/2.);
    vertbar = gGeoManager->MakeBox("vertbar", active_material, fScintBarY/2., fScintBarX/2., fScintBarZ/2.);
    horibar->SetVisibility(kTRUE);
    vertbar->SetVisibility(kTRUE);
    if(fActiveHCALMaterial){
        AddSensitiveVolume(horibar);
        AddSensitiveVolume(vertbar);
    }
    horibar->SetLineColor(kGreen);
    vertbar->SetLineColor(kGreen);

    //layer index, has both the sensitive and passive layers


   //Build horizontal layer
    
    unsigned short layerid = 0;
    Double_t z_index = 0;

    Double_t offset_x = static_cast<Double_t>(fNmodulesX)/2. * fModule_Size_X;
    Double_t offset_y = static_cast<Double_t>(fNmodulesY)/2. * fModule_Size_Y;
    //Build calorimeter
        //Build module by module
        
        for(int mod_x=0;mod_x<fNmodulesX;mod_x++){
            for(int mod_y=0;mod_y<fNmodulesY;mod_y++){
                //Build layer by layer
                while(layerid < fnSamplings){
                    z_index += fPassiveLayerZ/2.;
                    //Add passive absorber plate
	                tHCAL->AddNode(passive_plate,0,new TGeoTranslation(-offset_x + (static_cast<Double_t>(mod_x)+0.5)*fModule_Size_X, -offset_y + (static_cast<Double_t>(mod_y)+0.5)*fModule_Size_Y, z_index));
                    z_index += fPassiveLayerZ/2.;
                    z_index += fScintBarZ/2.;
                    //Place bars
                    for(UInt_t barid=0;barid<fNBarsPerLayer;barid++){
                        //horizontal bar if even, vertical if odd
                        if(layerid%2) tHCAL->AddNode(horibar, 2e6+1e5*mod_x+1e4*mod_y+1e3*layerid+static_cast<Double_t>(barid),new TGeoTranslation(-offset_x + (mod_x+0.5)*fModule_Size_X ,-offset_y + (mod_y)*fModule_Size_Y + (static_cast<Double_t>(barid)+0.5)*fScintBarY  , z_index));
			else          tHCAL->AddNode(vertbar, 2e6+1e5*mod_x+1e4*mod_y+1e3*layerid+static_cast<Double_t>(barid),new TGeoTranslation(-offset_x + (mod_x)*fModule_Size_X + (static_cast<Double_t>(barid)+0.5)*fScintBarX  ,-offset_y + (mod_y+0.5)*fModule_Size_Y , z_index));
                    }
                    z_index += fScintBarZ/2.;
                    layerid ++;
                }
            }

    }

	//Old code

    //finish assembly and position
    TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tHCAL->GetShape());
    Double_t totLength = asmb->GetDZ();
    top->AddNode(tHCAL, 1, new TGeoTranslation(0, 0,zStartHCAL+totLength));




    // //gROOT->SetBatch(true);

    //    TCanvas* c1 = new TCanvas("HCALCanvas", "", 800, 800);
    //    c1->cd();

    //    TView3D* tview = (TView3D*) TView::CreateView();
    //    tview->SetRange(-fXMax*1.2, -fYMax*1.2, 2500, fXMax*1.2, fYMax*1.2, 3800);
    //    tview->RotateView(0, 90, c1);

    //    tHCAL->Draw("ogle");
    //    c1->SaveAs(TString("HCAL.eps"));
    //    c1->SaveAs(TString("HCAL.pdf"));


}

HCALPoint* HCAL::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode)
{
  TClonesArray& clref = *fHCALPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "HCAL hit called"<< pos.z()<<endl;
  return new(clref[size]) HCALPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode);
}
