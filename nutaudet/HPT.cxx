//
//  TargetTracker.cxx
//  
//
//  Created by Annarita Buonaura.
//  Design3 added by Antonio Iuliano for HPT
//

#include "HPT.h"
#include "NuTauMudet.h"
#include "HptPoint.h"
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

Hpt::Hpt()
  : FairDetector("HighPrecisionTrackers",kTRUE, ktauHpt),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fHptPointCollection(new TClonesArray("HptPoint"))
{
}

Hpt::Hpt(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,const char* Title)
  : FairDetector(name, Active, ktauHpt),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fHptPointCollection(new TClonesArray("HptPoint"))
{
  DimX = DX;
  DimY = DY;
  DimZ = DZ;
}

Hpt::~Hpt()
{
    if (fHptPointCollection) {
        fHptPointCollection->Delete();
        delete fHptPointCollection;
    }
}

void Hpt::Initialize()
{
    FairDetector::Initialize();
}

//Sets the dimension of the Magnetic Spectrometer volume in which the HPT are placed
void Hpt::SetZsize(const Double_t Mudetsize)
{
  zSizeMudet = Mudetsize;
}

//Sets the dimension of the concrete base on which the external couples of HPTs are placed
void Hpt::SetConcreteBaseDim(Double_t X, Double_t Y, Double_t Z)
{
  fConcreteX = X;
  fConcreteY = Y;
  fConcreteZ = Z;
}

void Hpt::SetDistanceHPTs(Double_t dd) //only for geometry 3
{
  fDistance = dd;
}

void Hpt::SetHPTNumber(Int_t nHPT)
{
 fnHPT = nHPT;
}

void Hpt::SetDesign(Int_t Design)
{
  fDesign = Design;
}

void Hpt::SetSurroundingDetHeight(Double_t height)
{ 
 fSRHeight = height;
}

void Hpt::GetMagnetGeometry(Double_t EmuzC, Double_t EmuY)
{
  fmagnetcenter = EmuzC;
  fmagnety = EmuY;
}

void Hpt::GetNumberofTargets(Int_t ntarget) //in nutautargetdesign 3 more than one neutrino target are considered
{
   fntarget = ntarget;
} 

// -----   Private method InitMedium 
Int_t Hpt::InitMedium(const char* name)
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

void Hpt::SetSciFiParam(Double_t scifimat_width_, Double_t scifimat_hor_,  Double_t scifimat_vert_, 
                           Double_t scifimat_z_, Double_t support_z_, Double_t honeycomb_z_)
{
    scifimat_width = scifimat_width_;
    scifimat_hor = scifimat_hor_;
    scifimat_vert = scifimat_vert_;
    scifimat_z = scifimat_z_;
    support_z = support_z_; 
    honeycomb_z = honeycomb_z_;
}

void Hpt::SetNumberSciFi(Int_t n_hor_planes_, Int_t n_vert_planes_)
{
  n_hor_planes = n_hor_planes_;
  n_vert_planes = n_vert_planes_;
}

void Hpt::SetHPTrackerParam(Double_t HPTX, Double_t HPTY, Double_t HPTZ)
{   
    HPTrackerX = HPTX;
    HPTrackerY = HPTY;
    HPTrackerZ = HPTZ; 
}

void Hpt::ConstructGeometry()
{  
    InitMedium("HPTgas");
    TGeoMedium *HPTmat =gGeoManager->GetMedium("HPTgas");

    InitMedium("Concrete");
    TGeoMedium *Conc =gGeoManager->GetMedium("Concrete");

    // cout << "zSizeMudet = " << zSizeMudet << endl;
    if (fDesign < 3){
    TGeoVolume *volMudetBox = gGeoManager->GetVolume("volNuTauMudet");
    TGeoBBox *HPT = new TGeoBBox("HPT", DimX/2, DimY/2, DimZ/2);
    TGeoVolume *volHPT = new TGeoVolume("volHPT",HPT,HPTmat);
    volHPT->SetLineColor(kBlue-5);
    AddSensitiveVolume(volHPT);
    
    TGeoBBox *Cbase = new TGeoBBox("Cbase", fConcreteX/2, fConcreteY/2, fConcreteZ/2);
    TGeoVolume *volCbase = new TGeoVolume("volCbase",Cbase,Conc);
    volCbase->SetLineColor(kOrange-7);

    //1 closer to Goliath
    volMudetBox->AddNode(volHPT,1,new TGeoTranslation(0,0,-zSizeMudet/2 + DimZ/2));
    volMudetBox->AddNode(volCbase,1,new TGeoTranslation(0,-DimY/2-fConcreteY/2,-zSizeMudet/2 + DimZ/2));

    //2 closer to Arm1
    //NB: 55 cm is the distance between the borders of the last 2 drift tubes
    volMudetBox->AddNode(volHPT,2,new TGeoTranslation(0,0,-zSizeMudet/2 + 3*DimZ/2 +55*cm));
    volMudetBox->AddNode(volCbase,2,new TGeoTranslation(0,-DimY/2-fConcreteY/2,-zSizeMudet/2 + 3*DimZ/2 +55*cm));
   
    //Central Drift tubes // 3 closer to Arm1, 4 closer to Arm2
    volMudetBox->AddNode(volHPT,3,new TGeoTranslation(0,0,-72*cm/2 - DimZ/2));

    //NB: 72cm is the distance between the borders of the central drift tubes
    volMudetBox->AddNode(volHPT,4,new TGeoTranslation(0,0,72*cm/2 + DimZ/2));
   
    
    //After spectro Drift Tubes 5 closer to Arm, 6 closer to decay vessel
    volMudetBox->AddNode(volHPT,5,new TGeoTranslation(0,0,zSizeMudet/2 - 3*DimZ/2 - 55*cm));
    volMudetBox->AddNode(volCbase,5,new TGeoTranslation(0,-DimY/2-fConcreteY/2,zSizeMudet/2 - 3*DimZ/2 - 55*cm));    

    volMudetBox->AddNode(volHPT,6,new TGeoTranslation(0,0,zSizeMudet/2 - DimZ/2));
    volMudetBox->AddNode(volCbase,6,new TGeoTranslation(0,-DimY/2-fConcreteY/2,zSizeMudet/2 - DimZ/2));

    }
    if (fDesign == 3){
        //Trackers that in design 3 follow the target --------------------------------------------------------------------------------------    
        TGeoVolume *volMagRegion=gGeoManager->GetVolume("volMagRegion"); 
        TGeoVolume *volTarget =gGeoManager->GetVolume("volTarget");
        TGeoVolume *tTauNuDet = gGeoManager->GetVolume("tTauNuDet");  

        Double_t DZMagnetizedRegion = ((TGeoBBox*) volMagRegion->GetShape())->GetDZ() *2;  
        Double_t DYMagnetizedRegion = ((TGeoBBox*) volMagRegion->GetShape())->GetDY() *2;  
        Double_t DXMagnetizedRegion = ((TGeoBBox*) volMagRegion->GetShape())->GetDX() *2;      

        Double_t DZTarget = ((TGeoBBox*) volTarget->GetShape())->GetDZ() *2;  

        //HPT is DownStreamTracker
        TGeoBBox *DT = new TGeoBBox("DT", DimX/2, DimY/2, DimZ/2);
        TGeoVolume *volDT = new TGeoVolume("volDT",DT,HPTmat); 
        volDT->SetLineColor(kBlue-5);
        
        // Creating of SciFi modules in HPT   
        InitMedium("CarbonComposite");
        TGeoMedium *CarbonComposite = gGeoManager->GetMedium("CarbonComposite");

        InitMedium("SciFiMat");
        TGeoMedium *SciFiMat = gGeoManager->GetMedium("SciFiMat");

        InitMedium("Airex");
        TGeoMedium *Airex = gGeoManager->GetMedium("Airex"); 

        //Support Carbon Composite
        TGeoBBox* HPT_support_box = new TGeoBBox("HPT_support_box", HPTrackerX / 2, HPTrackerY / 2, support_z / 2);
        TGeoVolume* HPT_support_volume = new TGeoVolume("HPT_support", HPT_support_box, CarbonComposite);
        HPT_support_volume->SetLineColor(kGray - 2);
        HPT_support_volume->SetVisibility(1);

        //Honeycomb Airex (or Nomex)
        TGeoBBox* HPT_honeycomb_box = new TGeoBBox("HPT_honeycomb_box", HPTrackerX / 2, HPTrackerY / 2, honeycomb_z / 2);
        TGeoVolume* HPT_honeycomb_volume = new TGeoVolume("HPT_honeycomb", HPT_honeycomb_box, Airex);
        HPT_honeycomb_volume->SetLineColor(kYellow);
        HPT_honeycomb_volume->SetVisibility(1);

        //SciFi planes
        TGeoBBox* HPT_scifi_plane_hor_box = new TGeoBBox("HPT_scifi_plane_hor_box", HPTrackerX / 2, HPTrackerY / 2, scifimat_z / 2);
        TGeoVolume* HPT_scifi_plane_hor_volume = new TGeoVolume("HPT_scifi_plane_hor", HPT_scifi_plane_hor_box, SciFiMat);
        HPT_scifi_plane_hor_volume->SetVisibility(1);

        TGeoBBox* HPT_scifi_plane_vert_box = new TGeoBBox("HPT_scifi_plane_vert_box", HPTrackerX / 2, HPTrackerY / 2, scifimat_z / 2);
        TGeoVolume* HPT_scifi_plane_vert_volume = new TGeoVolume("HPT_scifi_plane_vert", HPT_scifi_plane_vert_box, SciFiMat);
        HPT_scifi_plane_vert_volume->SetVisibility(1);

        //SciFi mats
        TGeoBBox* HPT_scifimat_hor_box = new TGeoBBox("HPT_scifimat_hor_box", scifimat_hor / 2, scifimat_width / 2, scifimat_z / 2);
        TGeoVolume* HPT_scifimat_hor_volume = new TGeoVolume("HPT_scifimat_hor", HPT_scifimat_hor_box, SciFiMat);
        HPT_scifimat_hor_volume->SetLineColor(kCyan);

        TGeoBBox* HPT_scifimat_vert_box = new TGeoBBox("HPT_scifimat_vert_box", scifimat_width / 2, scifimat_vert / 2, scifimat_z / 2);
        TGeoVolume* HPT_scifimat_vert_volume = new TGeoVolume("HPT_scifimat_vert", HPT_scifimat_vert_box, SciFiMat);
        HPT_scifimat_vert_volume->SetLineColor(kGreen);

        AddSensitiveVolume(HPT_scifimat_hor_volume);
        AddSensitiveVolume(HPT_scifimat_vert_volume);

        // Creating physical volumes and multiply 
        for (int i = 0; i < n_hor_planes; i++){
            HPT_scifi_plane_hor_volume->AddNode(HPT_scifimat_hor_volume, i+1, new TGeoTranslation(0, (-(n_hor_planes-1)/2.0 + i)*scifimat_width, 0));
        }
        for (int i = 0; i < n_vert_planes; i++){
            HPT_scifi_plane_vert_volume->AddNode(HPT_scifimat_vert_volume, 100+i+1 , new TGeoTranslation((-(n_vert_planes-1)/2.0 + i)*scifimat_width, 0, 0));
        }

        volDT->AddNode(HPT_support_volume,     0, new TGeoTranslation(0, 0, - DimZ / 2 + support_z / 2));
        volDT->AddNode(HPT_scifi_plane_hor_volume, 0, new TGeoTranslation(0, 0, - DimZ / 2 + support_z + scifimat_z / 2));
        volDT->AddNode(HPT_scifi_plane_vert_volume, 0, new TGeoTranslation(0, 0, - DimZ / 2 + support_z + scifimat_z + scifimat_z / 2));
        volDT->AddNode(HPT_honeycomb_volume,   0, new TGeoTranslation(0, 0, - DimZ / 2 + support_z + 2 * scifimat_z + honeycomb_z / 2));
        volDT->AddNode(HPT_support_volume,     1, new TGeoTranslation(0, 0, - DimZ / 2 + support_z + 2 * scifimat_z + honeycomb_z + support_z / 2));
        //////////////////////////////////////////////////////////////

        Double_t first_DT_position = -DZMagnetizedRegion/2 + DZTarget + DimZ/2;
        for(int i=0;i<fnHPT;i++){
            for (int j = 0; j < fntarget; j++){
                volMagRegion->AddNode(volDT,(i+1)*1000+j*fnHPT,new TGeoTranslation(0,0, first_DT_position + i*(fDistance+DimZ) + j*(DZTarget+ fnHPT * DimZ + (fnHPT-1)*fDistance)));              
            }
        }
    }
}

Bool_t  Hpt::ProcessHits(FairVolume* vol)
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
    if ( gMC->IsTrackExiting()     ||
         gMC->IsTrackStop()        ||
         gMC->IsTrackDisappeared() ){
        if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();

        gMC->CurrentVolID(fVolumeID);
        Int_t detID = fVolumeID;
        Int_t TTstationID;
        gMC->CurrentVolOffID(2, TTstationID);
        fVolumeID = TTstationID + detID;

        TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     

        AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean), 
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), 
               fTime, fLength,fELoss, pdgCode);
            
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(ktauRpc);
    }
    
    return kTRUE;
}

void Hpt::EndOfEvent()
{
    fHptPointCollection->Clear();
}


void Hpt::Register()
{
    
    /** This will create a branch in the output tree called
     HptPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("HptPoint", "Hpt",
                                          fHptPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------
// -----   returns hpt, arm, rpc numbers -----------------------------------
void Hpt::DecodeVolumeID(Int_t detID,int &nHPT, int &nplane, Bool_t &ishor)
{
   nHPT = detID/1000;
   int idir = (detID - nHPT*1000)/100;

   if (idir == 1) ishor = kFALSE;
   else if (idir == 0) ishor = kTRUE;

   nplane = (detID - nHPT*1000 - idir*100);
  

}

TClonesArray* Hpt::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fHptPointCollection; }
    else { return NULL; }
}

void Hpt::Reset()
{
    fHptPointCollection->Clear();
}


HptPoint* Hpt::AddHit(Int_t trackID, Int_t detID,
                        TVector3 pos, TVector3 mom,
                        Double_t time, Double_t length,
					    Double_t eLoss, Int_t pdgCode)

{
    TClonesArray& clref = *fHptPointCollection;
    Int_t size = clref.GetEntriesFast();

    return new(clref[size]) HptPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode);
}


ClassImp(Hpt)
