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
{}

PixelModules::PixelModules(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,Int_t nSl,const char* Title)
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


void PixelModules::SetSiliconStationPositions(Int_t nstation, Double_t posx, Double_t posy, Double_t posz){
 xs[nstation] = posx;
 ys[nstation] = posy;
 zs[nstation] = posz;
}

void PixelModules::SetSiliconStationAngles(Int_t nstation, Double_t anglex, Double_t angley, Double_t anglez){
 xangle[nstation] = anglex;
 yangle[nstation] = angley;
 zangle[nstation] = anglez;
}

void PixelModules::SetSiliconSlicesNumber(Int_t nSl){
	nSlices=nSl;
        if(nSlices==1){
		nSi=nSi1;
	}
	else if(nSlices=10){
	nSi=nSi10;
	}
}

Double_t *PixelModules::GetPosSize1(){
	return new Double_t[nSi1];
}

Double_t *PixelModules::GetPosSize10(){
	return new Double_t[nSi10];
}

void PixelModules::SetPositionSize(){
	if(nSlices==1){
		xs=GetPosSize1();
		ys=GetPosSize1();
		zs=GetPosSize1();
		xangle=GetPosSize1();
		yangle=GetPosSize1();
		zangle=GetPosSize1();
	}
	else if(nSlices==10){
		xs=GetPosSize10();
		ys=GetPosSize10();
		zs=GetPosSize10();
		xangle=GetPosSize10();
		yangle=GetPosSize10();
		zangle=GetPosSize10();
		
	}
}


void PixelModules::ComputeDimZSlice(){
DimZThinSlice=DimZSithin/nSlices;
DimZThickSlice=DimZSithick/nSlices;
}



void PixelModules::SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox, Double_t SZPixel, Double_t D1short, Double_t D1long,Double_t SiliconDZthin,Double_t SiliconDZthick)
{
  SBoxX = SX;
  SBoxY = SY;
  SBoxZ = SZ;
  zBoxPosition = zBox;
  DimZPixelBox = SZPixel;
  Dim1Short = D1short;
  Dim1Long = D1long;
  SetSiliconDZ(SiliconDZthin, SiliconDZthick);
  ComputeDimZSlice();
  SetVertical();
  SetIDs();
  SetPositionSize();
}

Bool_t *PixelModules::GetVertical1(){
	return new Bool_t[nSi1];
}

Bool_t *PixelModules::GetVertical10(){
	return new Bool_t[nSi10];
}

void PixelModules::SetVertical(){
	if(nSlices==10){
		vertical=GetVertical10();
    		for(int i=0;i<nSi10;i++){
    		    vertical[i]=kFALSE;
    		    }
    		for(int i=0;i<3;i++){
    			for(int j =0;j<20;j++){
    		    vertical[i*40+j]=kTRUE;
    		    }
    		}
		}
	else{
		vertical=GetVertical1();
		vertical[0]=kTRUE;
		vertical[1]=kTRUE;
		vertical[2]=kFALSE;
		vertical[3]=kFALSE;
		vertical[4]=kTRUE;
		vertical[5]=kTRUE;
		vertical[6]=kFALSE;
		vertical[7]=kFALSE;
		vertical[8]=kTRUE;
		vertical[9]=kTRUE;
		vertical[10]=kFALSE;
		vertical[11]=kFALSE;
	}
}

Int_t *PixelModules::GetIDlist1(){
return new Int_t[12];
}

Int_t *PixelModules::GetIDlist10(){
return new Int_t[120];
}

Int_t* PixelModules::SetIDs(){
	switch(nSlices){
		
		case 1 : {
			PixelIDlist=GetIDlist1();
			PixelIDlist[0]=111;
			PixelIDlist[1]=112;
			PixelIDlist[2]=121;
			PixelIDlist[3]=122;
			PixelIDlist[4]=131;
			PixelIDlist[5]=132;
			PixelIDlist[6]=141;
			PixelIDlist[7]=142;
			PixelIDlist[8]=151;
			PixelIDlist[9]=152;
			PixelIDlist[10]=161;
			PixelIDlist[11]=162;
			}
		case 10: {
			PixelIDlist=GetIDlist10();	
    			//id convention: 1{a}{b}{c}, a = number of pair (from 1 to 6), b = element of the pair (1 or 2), c=slice (0 to 9)
    			int chi=0;
    			for(int i=1110;i<1130;i++){
    				PixelIDlist[chi]=i;
    				chi++;
    			}
    			
    			for(int i=1210;i<1230;i++){
    				PixelIDlist[chi]=i;
	    			chi++;
    			}

    			for(int i=1310;i<1330;i++){
    				PixelIDlist[chi]=i;
    				chi++;
    			}
    			for(int i=1410;i<1430;i++){
    				PixelIDlist[chi]=i;
	    			chi++;
    			}
    			for(int i=1510;i<1530;i++){
    				PixelIDlist[chi]=i;
    				chi++;
    			}
    			for(int i=1610;i<1630;i++){
	    			PixelIDlist[chi]=i;
    				chi++;
    			}
    			//Alternated pixel stations optimized for y and x measurements
}

}
return PixelIDlist;
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
   for (int istation = 0; istation < nSi; istation++){
     if (TMath::Abs(xs[istation]) > offsetxmax) offsetxmax = TMath::Abs(xs[istation]);
     if (TMath::Abs(ys[istation]) > offsetymax) offsetymax = TMath::Abs(ys[istation]);
    }
    TGeoVolumeAssembly *volPixelBox = new TGeoVolumeAssembly("volPixelBox");
    Double_t inimodZoffset(zs[0]-DimZSithick) ;//initial Z offset of Pixel Module 0 so as to avoid volume extrusion
    top->AddNode(volPixelBox, 1, new TGeoTranslation(0,0,zBoxPosition+ inimodZoffset)); //volume moved in


    TGeoBBox *Pixelythin = new TGeoBBox("Pixelythin", Dim1Short/2, Dim1Long/2, DimZThinSlice/2); //long along y
    TGeoVolume *volPixelythin = new TGeoVolume("volPixelythin",Pixelythin,Silicon); 
    volPixelythin->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixelythin);

    TGeoBBox *Pixelxthin = new TGeoBBox("Pixelxthin", (Dim1Long)/2, (Dim1Short)/2, DimZThinSlice/2); //long along x
    TGeoVolume *volPixelxthin = new TGeoVolume("volPixelxthin",Pixelxthin,Silicon); 
    volPixelxthin->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixelxthin);

    TGeoBBox *Pixelythick = new TGeoBBox("Pixelythick", Dim1Short/2, Dim1Long/2, DimZThickSlice/2); //long along y
    TGeoVolume *volPixelythick = new TGeoVolume("volPixelythick",Pixelythick,Silicon); 
    volPixelythick->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixelythick);

    TGeoBBox *Pixelxthick = new TGeoBBox("Pixelxthick", (Dim1Long)/2, (Dim1Short)/2, DimZThickSlice/2); //long along x
    TGeoVolume *volPixelxthick = new TGeoVolume("volPixelxthick",Pixelxthick,Silicon); 
    volPixelxthick->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixelxthick);
  
  ///////////////////////////////////////////////////////Passive material///////////////////////////////////////////////////////

    TGeoBBox *WindowBox = new TGeoBBox("WindowBox",Windowx/2, Windowy/2,DimZWindow/2);
    TGeoVolume *volWindow = new TGeoVolume("volWindow",WindowBox,Kapton);
    volWindow->SetLineColor(kGray);

    TGeoBBox *FrontEndx = new TGeoBBox("FrontEndx",Dim1Long/2, Dim1Short/2 ,FrontEndthick/2);
    TGeoVolume *volFrontEndx = new TGeoVolume("volFrontEndx",FrontEndx,Silicon);
    volFrontEndx->SetLineColor(kGray);

    TGeoBBox *FrontEndy = new TGeoBBox("FrontEndy",Dim1Short/2, Dim1Long/2 ,FrontEndthick/2);
    TGeoVolume *volFrontEndy = new TGeoVolume("volFrontEndy",FrontEndy,Silicon);
    volFrontEndy->SetLineColor(kGray);

    TGeoBBox *FlexCux = new TGeoBBox("FlexCux",Dim1Long/2, Dim1Short/2 ,FlexCuthick/2);
    TGeoVolume *volFlexCux = new TGeoVolume("volFlexCux",FlexCux,Copper);
    volFlexCux->SetLineColor(kGray);

    TGeoBBox *FlexCuy = new TGeoBBox("FlexCuy",Dim1Short/2, Dim1Long/2 ,FlexCuthick/2);
    TGeoVolume *volFlexCuy = new TGeoVolume("volFlexCuy",FlexCuy,Copper);
    volFlexCuy->SetLineColor(kGray);

    TGeoBBox *FlexKapx = new TGeoBBox("FlexKapx",Dim1Long/2, Dim1Short/2 ,FlexKapthick/2);
    TGeoVolume *volFlexKapx = new TGeoVolume("volFlexKapx",FlexKapx,Kapton);
    volFlexKapx->SetLineColor(kGray);

    TGeoBBox *FlexKapy = new TGeoBBox("FlexKapy",Dim1Short/2, Dim1Long/2 ,FlexKapthick/2);
    TGeoVolume *volFlexKapy = new TGeoVolume("volFlexKapy",FlexKapy,Kapton);
    volFlexKapy->SetLineColor(kGray);

////////////////////////////////////////////////////////End passive material////////////////////////////////////////////////////////////////

  volWindow->AddNode(0,0,new TGeoTranslation(0,0,-DimZPixelBox/2.-inimodZoffset-DimZWindow));

    for (Int_t ipixel = 0; ipixel < nSi; ipixel++){
      if (vertical[ipixel]){
		if(PixelIDlist[ipixel]) {
			if(PixelIDlist[ipixel]<1130 || (PixelIDlist[ipixel]>1219 && PixelIDlist[ipixel]<1620)){
				volPixelBox->AddNode(volPixelythick, PixelIDlist[ipixel], new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset)); //compensation for the Node offset
					}
			else {volPixelBox->AddNode(volPixelythin, PixelIDlist[ipixel], new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset)); 
//compensation for the Node offset}
			}
					}
		else volPixelBox->AddNode(volPixelythick, 9000, new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset)); 
//this else is used for debugging, if the number of slices isn't 10

		if((ipixel+nSlices)%9==1){
					volFrontEndy->AddNode(volFrontEndy, 0,new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset+DimZThickSlice+FrontEndthick));
					volFlexCuy->AddNode(volFlexCuy, 0,new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset+DimZThickSlice+FlexCuthick));
					volFlexKapy->AddNode(volFlexKapy, 0,new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset+DimZThickSlice+FlexKapthick));	
			}
		}
      else{ 
		if(PixelIDlist[ipixel]) 
			if(PixelIDlist[ipixel]<1130 || (PixelIDlist[ipixel]>1219 && PixelIDlist[ipixel]<1620)){
				volPixelBox->AddNode(volPixelxthick, PixelIDlist[ipixel], new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset));
														}
			else{
				volPixelBox->AddNode(volPixelxthin, PixelIDlist[ipixel], new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset));
				}
		
		else {
			volPixelBox->AddNode(volPixelxthick, 9000, new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset)); //debugging else for if nSlice!=10
			}

		if((ipixel+nSlices)%9==1){
					volFrontEndx->AddNode(volFrontEndx, 0,new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset+DimZThickSlice+FrontEndthick));
					volFlexCux->AddNode(volFlexCux, 0,new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset+DimZThickSlice+FlexCuthick));
					volFlexKapx->AddNode(volFlexKapx, 0,new TGeoTranslation(xs[ipixel],ys[ipixel],-DimZPixelBox/2.+ zs[ipixel]-inimodZoffset+DimZThickSlice+FlexKapthick));	
					}
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
