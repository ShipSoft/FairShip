//MuonTagger.cxx
//Muon Filter, sensitive layers interleaved with iron blocks

#include "MuonTagger.h"

#include "MuonTaggerPoint.h"

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
#include "TGeoMaterial.h"
#include "TGeoMedium.h"

#include "TParticle.h"
#include "TParticlePDG.h"
#include "TParticleClassPDG.h"
#include "TVirtualMCStack.h"

#include "FairVolume.h"
#include "FairGeoVolume.h"
#include "FairGeoNode.h"
#include "FairRootManager.h"
#include "FairGeoLoader.h"
#include "FairGeoInterface.h"
#include "FairGeoTransform.h"
#include "FairGeoMedia.h"
#include "FairGeoMedium.h"
#include "FairGeoBuilder.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"

#include "ShipDetectorList.h"
#include "ShipUnit.h"
#include "ShipStack.h"

#include "TGeoUniformMagField.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream,etc
#include <string.h>

using std::cout;
using std::endl;

using namespace ShipUnit;

MuonTagger::MuonTagger()
: FairDetector("MuonTagger", "",kTRUE),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fMuonTaggerPointCollection(new TClonesArray("MuonTaggerPoint"))
{
}

MuonTagger::MuonTagger(const char* name, const Double_t BX, const Double_t BY, const Double_t BZ,const Double_t zBox, Bool_t Active,const char* Title)
: FairDetector(name, true, kMuonTagger),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fMuonTaggerPointCollection(new TClonesArray("MuonTaggerPoint"))
{
    BoxX = BX;
    BoxY = BY;
    BoxZ = BZ;
    zBoxPosition = zBox;
}

MuonTagger::~MuonTagger()
{
    if (fMuonTaggerPointCollection) {
        fMuonTaggerPointCollection->Delete();
        delete fMuonTaggerPointCollection;
    }
}

void MuonTagger::Initialize()
{
    FairDetector::Initialize();
}

void MuonTagger::SetPassiveParameters(Double_t PX, Double_t PY, Double_t PTh)
{
  PasX = PX;
  PasY = PY;
  PasThickness = PTh;
}//setting paramters of passive layers

void MuonTagger::SetSensitiveParameters(Double_t SX, Double_t SY, Double_t STh)
{
  SensX = SX;
  SensY = SY;
  SensThickness = STh;
}//setting parameters of sensitive layers

// -----   Private method InitMedium
Int_t MuonTagger::InitMedium(const char* name)
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



void MuonTagger::ConstructGeometry()
{
  InitMedium("vacuum");
  TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");
  
  InitMedium("iron");
  TGeoMedium *Iron = gGeoManager->GetMedium("iron");

  InitMedium("RPCgas");
  TGeoMedium *RPCmat = gGeoManager->GetMedium("RPCgas");
  
  TGeoVolume *top= gGeoManager->GetTopVolume(); 

  TGeoBBox *MuonBox = new TGeoBBox(BoxX/2,BoxY/2,BoxZ/2);
  TGeoVolume *VMuonBox = new TGeoVolume("VMuonBox", MuonBox,vacuum);
  VMuonBox->SetTransparency(1);
  Double_t goliathcentre_to_beam = 178.6; //mm    
  
  top->AddNode(VMuonBox, 1, new TGeoTranslation(0, goliathcentre_to_beam*mm, zBoxPosition));

  //begin muon filter part
  
  TGeoBBox * Passive = new TGeoBBox(PasX/2, PasY/2, PasThickness/2);
  TGeoVolume * VPassive = new TGeoVolume("VPassive", Passive, Iron);
  VPassive->SetLineColor(kGreen+1);
  
  TGeoBBox * Sensitive = new TGeoBBox(SensX/2, SensY/2, SensThickness/2);
  TGeoVolume * VSensitive = new TGeoVolume("VSensitive", Sensitive, RPCmat);
  VSensitive->SetLineColor(kOrange-5);
  AddSensitiveVolume(VSensitive);
  
  const Int_t npassive = 5;
  const Int_t nsensitive = 6;

  Double_t zpassive;
  Double_t zsensitive;
  
  for (int n = 0; n < npassive; n++){
    // zpassive = n * (PasThickness + SensThickness);
    zpassive = n * (PasThickness + SensThickness) + PasThickness/2 + SensThickness; //the first layer is sensitive
    VMuonBox->AddNode(VPassive, n, new TGeoTranslation(0,0,-BoxZ/2 + zpassive));
}

  for (int n = 0; n < nsensitive; n++){
    //zsensitive = n * (PasThickness + SensThickness) + PasThickness/2 + SensThickness/2;
     zsensitive = n * (PasThickness + SensThickness) + SensThickness/2; 
      VMuonBox->AddNode(VSensitive, n, new TGeoTranslation(0,0,-BoxZ/2 + zsensitive));
  }
}



Bool_t  MuonTagger::ProcessHits(FairVolume* vol)
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
    
    // Create MuonTaggerPoint at exit of active volume
    if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       ||
        gMC->IsTrackDisappeared()   ) {
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
        fVolumeID = vol->getMCid();
	Int_t detID=0;
	gMC->CurrentVolID(detID);

	if (fVolumeID == detID) {
	  return kTRUE; }
	fVolumeID = detID;

	//gGeoManager->PrintOverlaps();		
	
	if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
	Int_t pdgCode = p->GetPdgCode();
	
        TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
        
	
	AddHit(fTrackID,fVolumeID, TVector3(xmean, ymean,  zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
               fELoss, pdgCode);
	
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(kMuonTagger);
    }
    
    return kTRUE;
}



void MuonTagger::EndOfEvent()
{
    fMuonTaggerPointCollection->Clear();
}


void MuonTagger::Register()
{
    
    /** This will create a branch in the output tree called
     TargetPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("MuonTaggerPoint", "MuonTagger",
                                          fMuonTaggerPointCollection, kTRUE);
}

TClonesArray* MuonTagger::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fMuonTaggerPointCollection; }
    else { return NULL; }
}

void MuonTagger::Reset()
{
    fMuonTaggerPointCollection->Clear();
}


MuonTaggerPoint* MuonTagger::AddHit(Int_t trackID,Int_t detID,
                           TVector3 pos, TVector3 mom,
                           Double_t time, Double_t length,
			    Double_t eLoss, Int_t pdgCode)
{
    TClonesArray& clref = *fMuonTaggerPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new(clref[size]) MuonTaggerPoint(trackID,detID, pos, mom,
					time, length, eLoss, pdgCode);
}
ClassImp(MuonTagger)








