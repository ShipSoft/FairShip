#include "splitcal.h"

#include "splitcalPoint.h"


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



#include <iostream>
using std::cout;
using std::endl;

splitcal::splitcal()
  : FairDetector("splitcal", kTRUE, kSplitCal),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fsplitcalPointCollection(new TClonesArray("splitcalPoint"))
{
}

splitcal::splitcal(const char* name, Bool_t active)
  : FairDetector(name, active, kSplitCal),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fsplitcalPointCollection(new TClonesArray("splitcalPoint"))
{
}

splitcal::~splitcal()
{
  if (fsplitcalPointCollection) {
    fsplitcalPointCollection->Delete();
    delete fsplitcalPointCollection;
  }
}

void splitcal::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  splitcalGeoPar* par=(splitcalGeoPar*)(rtdb->getContainer("splitcalGeoPar"));
}
// -----   Private method InitMedium 
Int_t splitcal::InitMedium(const char* name) 
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
Bool_t  splitcal::ProcessHits(FairVolume* vol)
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

  // Create splitcalPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    //fVolumeID = vol->getMCid();
    //cout << "splitcal proc "<< fVolumeID<<" "<<vol->GetName()<<" "<<vol->getVolumeId() <<endl;
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

    // Increment number of splitcal det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kSplitCal);

  }

  return kTRUE;
}

void splitcal::EndOfEvent()
{

  fsplitcalPointCollection->Clear();

}



void splitcal::Register()
{

  /** This will create a branch in the output tree called
      splitcalPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("splitcalPoint", "splitcal",
                                        fsplitcalPointCollection, kTRUE);

}


TClonesArray* splitcal::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fsplitcalPointCollection; }
  else { return NULL; }
}

void splitcal::Reset()
{
  fsplitcalPointCollection->Clear();
}

void splitcal::SetZStart(Double_t ZStart)
{
  fZStart=ZStart;
}
void splitcal::SetEmpty(Double_t Empty, Double_t BigGap, Double_t ActiveECAL_gas_gap, Double_t first_precision_layer,Double_t second_precision_layer, Double_t third_precision_layer, Double_t num_precision_layers)
{
  fEmpty=Empty;
  fBigGap=BigGap;  
  fActiveECAL_gas_gap= ActiveECAL_gas_gap;
  ffirst_precision_layer=first_precision_layer;  
  fsecond_precision_layer=second_precision_layer; 
  fthird_precision_layer=third_precision_layer;
  fnum_precision_layers=num_precision_layers; 

 
}

void splitcal::SetThickness(Double_t ActiveECALThickness, Double_t ActiveHCALThickness, Double_t FilterECALThickness,Double_t FilterECALThickness_first,  Double_t FilterHCALThickness,  Double_t ActiveECAL_gas_Thickness)
{

    fActiveECALThickness = ActiveECALThickness;
    fActiveHCALThickness = ActiveHCALThickness;
    fFilterECALThickness = FilterECALThickness;
    fFilterECALThickness_first = FilterECALThickness_first;
    fFilterHCALThickness = FilterHCALThickness;
    fActiveECAL_gas_Thickness= ActiveECAL_gas_Thickness;

}
void splitcal::SetMaterial(Double_t ActiveECALMaterial, Double_t ActiveHCALMaterial, Double_t FilterECALMaterial, Double_t FilterHCALMaterial)
{

    fActiveECALMaterial = ActiveECALMaterial;
    fActiveHCALMaterial = ActiveHCALMaterial;
    fFilterECALMaterial = FilterECALMaterial;
    fFilterHCALMaterial = FilterHCALMaterial;

}

void splitcal::SetNSamplings(Double_t nECALSamplings, Double_t nHCALSamplings)
{
  fnHCALSamplings=nHCALSamplings;
  fnECALSamplings=nECALSamplings;
}

void splitcal::SetXMax(Double_t xMax)
{
  fXMax=xMax;
}
void splitcal::SetYMax(Double_t yMax)
{
  fYMax=yMax;
}
void splitcal::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoVolume *tSplitCal = new TGeoVolumeAssembly("SplitCalDetector");

    InitMedium("iron");
    InitMedium("lead");
    InitMedium("Scintillator");
    InitMedium("argon");
    InitMedium("GEMmixture");
    
    TGeoMedium *A2 =gGeoManager->GetMedium("iron");
    TGeoMedium *A3 =gGeoManager->GetMedium("lead");
    TGeoMedium *A4 =gGeoManager->GetMedium("GEMmixture");    
    TGeoMedium *A1 =gGeoManager->GetMedium("Scintillator");



    Double_t zStartSplitCal = fZStart;
    
    TGeoVolume *newECALfilter[100];
    TGeoVolume *newECALdet[100];     
    TGeoVolume *newECALdet_gas[6];     
    const char* char_labelECALfilter[100];
    TString labelECALfilter; 
    const char* char_labelECALdet[100];
    TString labelECALdet;
    const char* char_labelECALdet_gas[6];
    TString labelECALdet_gas;

    TGeoVolume *newHCALfilter[100];
    TGeoVolume *newHCALdet[100];     
    const char* char_labelHCALfilter[100];
    TString labelHCALfilter; 
    const char* char_labelHCALdet[100];
    TString labelHCALdet;


     
    Double_t z_splitcal=0;
    Int_t i_nlayECAL_gas;

    for (i_nlayECAL_gas=0; i_nlayECAL_gas<1; i_nlayECAL_gas++){
      labelECALdet_gas="ECALdet_gas_";
      labelECALdet_gas+=i_nlayECAL_gas;
      char_labelECALdet_gas[i_nlayECAL_gas]=labelECALdet_gas;

      newECALdet_gas[i_nlayECAL_gas] = gGeoManager->MakeBox(char_labelECALdet_gas[i_nlayECAL_gas], A4, fXMax, fYMax, fActiveECAL_gas_Thickness/2);      
      AddSensitiveVolume(newECALdet_gas[i_nlayECAL_gas]);
      newECALdet_gas[i_nlayECAL_gas]->SetLineColor(kRed);

    }
    for (Int_t i_nlayECAL=0; i_nlayECAL<1; i_nlayECAL++){
      labelECALfilter="ECALfilter_";
      labelECALfilter+=i_nlayECAL;
      char_labelECALfilter[i_nlayECAL]=labelECALfilter;
      labelECALdet="ECALdet_";
      labelECALdet+=i_nlayECAL;
      char_labelECALdet[i_nlayECAL]=labelECALdet;
      if(i_nlayECAL==0){
	xfFilterECALThickness=fFilterECALThickness_first;
      }
      else
	{
	  xfFilterECALThickness=fFilterECALThickness;
	}
       
      // cout << "SplitCal Debug:" << z_splitcal << " " << i_nlayECAL << " " << i_nlayECAL_gas << " " << xfFilterECALThickness<< endl;
      newECALfilter[i_nlayECAL] = gGeoManager->MakeBox(char_labelECALfilter[i_nlayECAL], A3, fXMax, fYMax, xfFilterECALThickness/2);
      if(i_nlayECAL!=ffirst_precision_layer and i_nlayECAL!=fsecond_precision_layer and i_nlayECAL!=fthird_precision_layer){
        newECALdet[i_nlayECAL] = gGeoManager->MakeBox(char_labelECALdet[i_nlayECAL], A1, fXMax, fYMax, fActiveECALThickness/2);

        AddSensitiveVolume(newECALdet[i_nlayECAL]);
        newECALdet[i_nlayECAL]->SetLineColor(kGreen);
        newECALfilter[i_nlayECAL]->SetLineColor(kGray);
      }
    } 
    for (Int_t i_nlayECAL=0; i_nlayECAL<fnECALSamplings; i_nlayECAL++){
      z_splitcal+=xfFilterECALThickness/2;
      tSplitCal->AddNode(newECALfilter[0], 1, new TGeoTranslation(0, 0, z_splitcal));
      z_splitcal+=xfFilterECALThickness/2;      
      if(i_nlayECAL==0)z_splitcal+=fEmpty;
      if(i_nlayECAL==7)        z_splitcal+=fBigGap;
      i_nlayECAL_gas=-1000;
      if(i_nlayECAL==ffirst_precision_layer or i_nlayECAL==fsecond_precision_layer or i_nlayECAL==fthird_precision_layer){
       z_splitcal+=fActiveECAL_gas_Thickness/2;    
       if(i_nlayECAL==ffirst_precision_layer) i_nlayECAL_gas=0;
       if(i_nlayECAL==fsecond_precision_layer ){
	 if(fnum_precision_layers==2){
	  i_nlayECAL_gas=3;
         }
         else
       	{
         i_nlayECAL_gas=1;	 
	}
       }
       if(i_nlayECAL==fthird_precision_layer ){
	 if(fnum_precision_layers==2){
	  i_nlayECAL_gas=4;
         }
         else
       	{
         i_nlayECAL_gas=2;	 
	}
       }
       tSplitCal->AddNode(newECALdet_gas[0], 1000.+i_nlayECAL_gas , new TGeoTranslation(0, 0, z_splitcal));
       z_splitcal+=fActiveECAL_gas_Thickness/2;
       if(fnum_precision_layers==2){
        z_splitcal+=fActiveECAL_gas_gap;
        z_splitcal+=fActiveECAL_gas_Thickness/2;      
        if(i_nlayECAL==ffirst_precision_layer) i_nlayECAL_gas=1;
        if(i_nlayECAL==fsecond_precision_layer) i_nlayECAL_gas=3;
        tSplitCal->AddNode(newECALdet_gas[i_nlayECAL_gas], 1, new TGeoTranslation(0, 0, z_splitcal));
        z_splitcal+=fActiveECAL_gas_Thickness/2;
       }
      }
      else{ 
       z_splitcal+=fActiveECALThickness/2;      
       tSplitCal->AddNode(newECALdet[0], 2000.+i_nlayECAL, new TGeoTranslation(0, 0, z_splitcal));
       z_splitcal+=fActiveECALThickness/2;      
      }

      //      z_splitcal+=fEmpty;


    }
    for (Int_t i_nlayHCAL=0; i_nlayHCAL<1; i_nlayHCAL++){
      labelHCALfilter="HCALfilter_";
      labelHCALfilter+=i_nlayHCAL;
      char_labelHCALfilter[i_nlayHCAL]=labelHCALfilter;
      labelHCALdet="HCAL_det";
      labelHCALdet+=i_nlayHCAL;
      char_labelHCALdet[i_nlayHCAL]=labelHCALdet;
      newHCALfilter[i_nlayHCAL] = gGeoManager->MakeBox(char_labelHCALfilter[i_nlayHCAL], A2, fXMax, fYMax, fFilterHCALThickness/2);
      newHCALdet[i_nlayHCAL] = gGeoManager->MakeBox(char_labelHCALdet[i_nlayHCAL], A4, fXMax, fYMax, fActiveHCALThickness/2);

      AddSensitiveVolume(newHCALdet[i_nlayHCAL]);

      newHCALdet[i_nlayHCAL]->SetLineColor(kRed);
      newHCALfilter[i_nlayHCAL]->SetLineColor(kBlue);
    }
    for (Int_t i_nlayHCAL=0; i_nlayHCAL<fnHCALSamplings; i_nlayHCAL++){
      z_splitcal+=fFilterHCALThickness/2;
      tSplitCal->AddNode(newHCALfilter[i_nlayHCAL], 1, new TGeoTranslation(0, 0, z_splitcal));
      z_splitcal+=fFilterHCALThickness/2;      
      // z_splitcal+=fEmpty;
      z_splitcal+=fActiveHCALThickness/2;      
      tSplitCal->AddNode(newHCALdet[i_nlayHCAL], 1, new TGeoTranslation(0, 0, z_splitcal));
      z_splitcal+=fActiveHCALThickness/2;      
      // z_splitcal+=fEmpty;


    }
    


          //finish assembly and position
    TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tSplitCal->GetShape());
    Double_t totLength = asmb->GetDZ();
    top->AddNode(tSplitCal, 1, new TGeoTranslation(0, 0,zStartSplitCal+totLength));  
}

splitcalPoint* splitcal::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode)
{
  TClonesArray& clref = *fsplitcalPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "splitcal hit called"<< pos.z()<<endl;
  return new(clref[size]) splitcalPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode);
}

ClassImp(splitcal)
