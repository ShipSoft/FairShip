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
#include "TGeoNode.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoCompositeShape.h" //for boolean operations

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

void MuonTagger::SetPassiveParameters(Double_t PX, Double_t PY, Double_t PTh, Double_t PTh1)
{
  PasX = PX;
  PasY = PY;
  PasThicknessz[0] = PTh;
  PasThicknessz[1] = PTh;  
  PasThicknessz[2] = PTh1; 
  PasThicknessz[3] = PTh1;  
  PasThicknessz[4] = PTh1;  
  PasThickness = PTh;
  PasThickness1 = PTh1;
   
    
}//setting paramters of passive layers

void MuonTagger::SetSensitiveParameters(Double_t SX, Double_t SY, Double_t STh)
{
  SensX = SX;
  SensY = SY;
  SensThickness = STh;
}//setting parameters of sensitive layers

void MuonTagger::SetRPCz(Double_t RPC1z, Double_t RPC2z, Double_t RPC3z, Double_t RPC4z,  Double_t RPC5z)
{
  fRPCz[0] = RPC1z;
  fRPCz[1] = RPC2z;
  fRPCz[2] = RPC3z;
  fRPCz[3] = RPC4z;
  fRPCz[4] = RPC5z;
}

void MuonTagger::SetRPCThickness(Double_t RPCThickness)
{
  fRPCThickness = RPCThickness;
}

void MuonTagger::SetElectrodeThickness(Double_t ElectrodeThickness)
{
  fElectrodeThickness = ElectrodeThickness;
}

void MuonTagger::SetGapThickness(Double_t GapThickness)
{
  fGapThickness = GapThickness;
}

void MuonTagger::SetStripz(Double_t Stripz, Double_t Stripfoamz)
{
  fStripz = Stripz;
  fStripfoamz = Stripfoamz;
}

void MuonTagger::SetVStrip(Double_t Vstripx, Double_t Vstrip_L, Double_t Vstrip_R, Double_t Vstripoffset)
{
  fVstripx = Vstripx;
  fVstrip_L = Vstrip_L;
  fVstrip_R = Vstrip_R;
  fVstripoffset = Vstripoffset;
}

void MuonTagger::SetHStrip(Double_t Hstripy, Double_t Hstrip_ext, Double_t Hstripoffset)
{
  fHstripy = Hstripy;
  fHstrip_ext = Hstrip_ext;
  fHstripoffset = Hstripoffset;
}

void MuonTagger::SetNStrips(Int_t NVstrips, Int_t NHstrips)
{
  fNVstrips = NVstrips;
  fNHstrips = NHstrips;
}

void MuonTagger::SetHoleDimensions(Double_t HX, Double_t HY)
{
  HoleX = HX;
  HoleY = HY;
}

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
  InitMedium("air");
  TGeoMedium *air = gGeoManager->GetMedium("air");
  
  InitMedium("iron");
  TGeoMedium *Iron = gGeoManager->GetMedium("iron");

  InitMedium("copper");
  TGeoMedium *Copper = gGeoManager->GetMedium("copper");

  InitMedium("RPCgas");
  TGeoMedium *RPCmat = gGeoManager->GetMedium("RPCgas");
  
  InitMedium("PlasticFoam");
  TGeoMedium *Foam = gGeoManager->GetMedium("PlasticFoam");
     
  InitMedium("Bakelite");
  TGeoMedium *bakelite = gGeoManager->GetMedium("Bakelite");
  
  TGeoVolume *top= gGeoManager->GetTopVolume(); 

  TGeoVolumeAssembly *VMuonBox = new TGeoVolumeAssembly("VMuonBox");
  VMuonBox->SetTransparency(1);
  Double_t goliathcentre_to_beam = 178.6; //mm   
  Double_t walldisalignment = 15; //mm, all walls but one were disaligned with respect to the nominal beam position
  Double_t eps = 0.00001;     
  
  TGeoBBox *GapBox = new TGeoBBox(SensX/2,SensY/2,fGapThickness/2-eps);  
  TGeoVolume *Gap = new TGeoVolume("Gap", GapBox,RPCmat);  
  Gap->SetLineColor(kGreen);
  AddSensitiveVolume(Gap); 
  
  TGeoBBox *GroundBox = new TGeoBBox(SensX/2,SensY/2,fStripz/2-eps);  
  TGeoVolume *Ground = new TGeoVolume("Ground", GroundBox,Copper);  
  Ground->SetLineColor(kOrange);
  
  TGeoBBox *ElectrodeBox = new TGeoBBox(SensX/2,SensY/2,fElectrodeThickness/2-eps);  
  TGeoVolume *Electrode = new TGeoVolume("Electrode", ElectrodeBox,bakelite);   
  Electrode->SetLineColor(kBlue);
  
  TGeoBBox *VStripBox = new TGeoBBox(fVstripx/2,SensY/2,fStripz/2-eps);  
  TGeoVolume *Vstrip = new TGeoVolume("Vstrip", VStripBox,Copper); 
  Vstrip->SetLineColor(kOrange);
  
  TGeoBBox *VFoamBox = new TGeoBBox(fVstripx/2,SensY/2,fStripfoamz/2-eps);  
  TGeoVolume *VFoam = new TGeoVolume("VFoam", VFoamBox,Foam);     
  VFoam->SetLineColor(kRed);
  
  TGeoBBox *VStripBox_L = new TGeoBBox(fVstrip_L/2,SensY/2,fStripz/2-eps);  
  TGeoVolume *Vstrip_L = new TGeoVolume("Vstrip_L", VStripBox_L,Copper); 
  Vstrip_L->SetLineColor(kGray);
  
  TGeoBBox *VFoamBox_L = new TGeoBBox(fVstrip_L/2,SensY/2,fStripfoamz/2-eps);  
  TGeoVolume *VFoam_L = new TGeoVolume("VFoam_L", VFoamBox_L,Foam); 
  VFoam_L->SetLineColor(kRed); 
      
  TGeoBBox *VStripBox_R = new TGeoBBox(fVstrip_R/2,SensY/2,fStripz/2-eps);  
  TGeoVolume *Vstrip_R = new TGeoVolume("Vstrip_R", VStripBox_R,Copper);  
  Vstrip_R->SetLineColor(kGray);
  
  TGeoBBox *VFoamBox_R = new TGeoBBox(fVstrip_R/2,SensY/2,fStripfoamz/2-eps);  
  TGeoVolume *VFoam_R = new TGeoVolume("VFoam_R", VFoamBox_R,Foam);   
  VFoam_R->SetLineColor(kYellow);
  
  TGeoBBox *HStripBox = new TGeoBBox(SensX/2,fHstripy/2,fStripz/2-eps);  
  TGeoVolume *Hstrip = new TGeoVolume("Hstrip", HStripBox,Copper); 
  Hstrip->SetLineColor(kOrange);
  
  TGeoBBox *HFoamBox = new TGeoBBox(SensX/2,fHstripy/2,fStripfoamz/2-eps);  
  TGeoVolume *HFoam = new TGeoVolume("HFoam", HFoamBox,Foam);    
  HFoam->SetLineColor(kRed);    
  
  TGeoBBox *HStripBox_ext = new TGeoBBox(SensX/2,fHstrip_ext/2,fStripz/2-eps);  
  TGeoVolume *Hstrip_ext = new TGeoVolume("Hstrip_ext", HStripBox_ext,Copper); 
  Hstrip_ext->SetLineColor(kGray);  
    
  TGeoBBox *HFoamBox_ext = new TGeoBBox(SensX/2,fHstrip_ext/2,fStripfoamz/2-eps);  
  TGeoVolume *HFoam_ext = new TGeoVolume("HFoam_ext", HFoamBox_ext,Foam);  
  HFoam_ext->SetLineColor(kRed);    
  
  // 15.443 mm required to align top with survey measurement    
  top->AddNode(VMuonBox, 1, new TGeoTranslation(0, goliathcentre_to_beam*mm + 15.443*mm, zBoxPosition));

  //begin muon filter part
  //hole for the passive layers.
  TGeoBBox *inbox = new TGeoBBox("inbox",HoleX/2,HoleY/2,PasThickness/2 + SensThickness/2); 
  inbox->SetName("T");
  
  TGeoBBox *inbox1 = new TGeoBBox("inbox1",HoleX/2,HoleY/2,PasThickness1/2 + SensThickness/2); 
  inbox1->SetName("T1");
  
  TGeoTranslation *holeposition = new TGeoTranslation(0, -(goliathcentre_to_beam*mm + 16.443*mm),0);
  holeposition->SetName("holepos");
  holeposition->RegisterYourself();
  //passive layers
  TGeoBBox * Passive = new TGeoBBox(PasX/2, PasY/2, PasThickness/2);
  Passive->SetName("P");
  TGeoCompositeShape *SubtractionPassive = new TGeoCompositeShape("SubtractionPassive", "P-T:holepos");

  TGeoBBox * Passive1 = new TGeoBBox(PasX/2, PasY/2, PasThickness1/2);
  Passive1->SetName("P1");
  TGeoCompositeShape *SubtractionPassive1 = new TGeoCompositeShape("SubtractionPassive1", "P1-T1:holepos");

  TGeoVolume * VPassive = new TGeoVolume("VPassive", SubtractionPassive, Iron);
  VPassive->SetLineColor(kGreen+1);

  TGeoVolume * VPassive1 = new TGeoVolume("VPassive1", SubtractionPassive1, Iron);     
  VPassive1->SetLineColor(kGreen+1);
   
  //sensitive layers
  TGeoBBox * Sensitive = new TGeoBBox(SensX/2, SensY/2, fRPCThickness/2);
  TGeoVolume * VSensitive1 = new TGeoVolume("VSensitive1", Sensitive, air);  
  TGeoVolume * VSensitive2 = new TGeoVolume("VSensitive2", Sensitive, air);
  TGeoVolume * VSensitive3 = new TGeoVolume("VSensitive3", Sensitive, air);
  TGeoVolume * VSensitive4 = new TGeoVolume("VSensitive4", Sensitive, air);
  TGeoVolume * VSensitive5 = new TGeoVolume("VSensitive5", Sensitive, air);
  
  TGeoVolume * VSensitive[5]={VSensitive1,VSensitive2,VSensitive3,VSensitive4,VSensitive5};
  for (int i=0;i<5;i++) {    
     VSensitive[i]->SetLineColor(kOrange-5);
  }
  
  Double_t zpassive;
  Double_t zsensitive;
  
  const Int_t npassive = 5;
  const Int_t nsensitive = 5;
  const Int_t npassiveshort = 3;
  
  for (int n = 0; n < npassive; n++){
    if (n==0) {
       VMuonBox->AddNode(VPassive, n+1, new TGeoTranslation(0,0,fRPCz[n]-PasThicknessz[n]/2-7.5)); }
    else { 
       if (n==1) { VMuonBox->AddNode(VPassive, n+1, new TGeoTranslation(0,0,fRPCz[n]-PasThicknessz[n]/2.-(fRPCz[n]-fRPCz[n-1]-PasThicknessz[n])/2.)); }
       //else if (n==npassive-1) VMuonBox->AddNode(VPassive1, n+1, new TGeoTranslation(0,walldisalignment,fRPCz[n]-PasThicknessz[n]/2.-(fRPCz[n]-fRPCz[n-1]-PasThicknessz[n])/2.)); //last wall had been disaligned with respect to the others
       else{
         VMuonBox->AddNode(VPassive1, n+1, new TGeoTranslation(0,0,fRPCz[n]-PasThicknessz[n]/2.-(fRPCz[n]-fRPCz[n-1]-PasThicknessz[n])/2.)); }  
    }
  }

  for (int n = 1; n < nsensitive+1; n++){
    TGeoTranslation trans; 
    trans.SetTranslation(0,0,0);
    VMuonBox->AddNode(VSensitive[n-1], n, new TGeoTranslation(0,0,fRPCz[n-1]));
    VSensitive[n-1]->AddNode(Ground,10000*n+2000,new TGeoTranslation(0,0,-fGapThickness/2-fElectrodeThickness-0.025-fStripz-fStripfoamz-fStripz/2));
    VSensitive[n-1]->AddNode(Electrode,10000*n+3000,new TGeoTranslation(0,0,-fGapThickness/2-0.025-fElectrodeThickness/2));
    VSensitive[n-1]->AddNode(Gap,10000*n+4000,new TGeoTranslation(0,0,0));	
    VSensitive[n-1]->AddNode(Electrode,10000*n+5000,new TGeoTranslation(0,0,fGapThickness/2+0.025+fElectrodeThickness/2));	
    VSensitive[n-1]->AddNode(Ground,10000*n+6000,new TGeoTranslation(0,0,+fGapThickness/2+fElectrodeThickness+0.025+fStripz+fStripfoamz+fStripz/2));	    
    for (int m = 1; m < fNHstrips+1; m++) {
	if (m == 1){
	       VSensitive[n-1]->AddNode(HFoam_ext,10000*n+7000+m,new TGeoTranslation(0,SensY/2-fHstrip_ext/2,-fGapThickness/2-fElectrodeThickness-0.025-fStripz-fStripfoamz/2));	    
	       VSensitive[n-1]->AddNode(Hstrip_ext,10000*n+m,new TGeoTranslation(0,SensY/2-fHstrip_ext/2,-fGapThickness/2-fElectrodeThickness-0.025-fStripz/2));
	}
        else {
	   if (m==fNHstrips) {
	       VSensitive[n-1]->AddNode(HFoam_ext,10000*n+7000+m,new TGeoTranslation(0,SensY/2-fHstripoffset*(m-1)-fHstripy*(m-2)-3*fHstrip_ext/2,-fGapThickness/2-fElectrodeThickness-0.025-fStripz-fStripfoamz/2));	    
	       VSensitive[n-1]->AddNode(Hstrip_ext,10000*n+m,new TGeoTranslation(0,SensY/2-fHstripoffset*(m-1)-fHstripy*(m-2)-3*fHstrip_ext/2,-fGapThickness/2-fElectrodeThickness-0.025-fStripz/2));	   	   
	   }
	   else {	   
	       VSensitive[n-1]->AddNode(HFoam,10000*n+7000+m,new TGeoTranslation(0,SensY/2-fHstrip_ext-fHstripoffset*(m-1)-fHstripy*(m-2)-fHstripy/2,-fGapThickness/2-fElectrodeThickness-0.025-fStripz-fStripfoamz/2));	    
	       VSensitive[n-1]->AddNode(Hstrip,10000*n+m,new TGeoTranslation(0,SensY/2-fHstrip_ext-fHstripoffset*(m-1)-fHstripy*(m-2)-fHstripy/2,-fGapThickness/2-fElectrodeThickness-0.025-fStripz/2));
	   }   
        }
    }
    for (int m = 1; m < fNVstrips+1; m++) {	
	if (m == 1) {	    
	       VSensitive[n-1]->AddNode(Vstrip_R,10000*n+1000+m,new TGeoTranslation(SensX/2-fVstrip_R/2,0,fGapThickness/2+fElectrodeThickness+0.025+fStripz/2));
	       VSensitive[n-1]->AddNode(VFoam_R,10000*n+8000+m,new TGeoTranslation(SensX/2-fVstrip_R/2,0,fGapThickness/2+fElectrodeThickness+0.025+fStripz+fStripfoamz/2));
	}
	else {
	   if (m == fNVstrips ) {
	          VSensitive[n-1]->AddNode(Vstrip_L,10000*n+1000+m,new TGeoTranslation(SensX/2-fVstripoffset*(m-1)-fVstripx*(m-2)-fVstrip_R-fVstrip_L/2,0,fGapThickness/2+fElectrodeThickness+0.025+fStripz/2));
	          VSensitive[n-1]->AddNode(VFoam_L,10000*n+8000+m,new TGeoTranslation(SensX/2-fVstripoffset*(m-1)-fVstripx*(m-2)-fVstrip_R-fVstrip_L/2,0,fGapThickness/2+fElectrodeThickness+0.025+fStripz+fStripfoamz/2));	
	   }
	   else {	
	          VSensitive[n-1]->AddNode(Vstrip,10000*n+1000+m,new TGeoTranslation(SensX/2-fVstripoffset*(m-1)-fVstripx*(m-2)-fVstripx/2-fVstrip_R,0,fGapThickness/2+fElectrodeThickness+0.025+fStripz/2));
	          VSensitive[n-1]->AddNode(VFoam,10000*n+8000+m,new TGeoTranslation(SensX/2-fVstripoffset*(m-1)-fVstripx*(m-2)-fVstripx/2-fVstrip_R,0,fGapThickness/2+fElectrodeThickness+0.025+fStripz+fStripfoamz/2));	
	   }
	}   
     }    
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
       
	gMC->CurrentVolID(fVolumeID);
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

void MuonTagger::EndPoints(Int_t fDetectorID, TVector3 &vbot, TVector3 &vtop) {
// method to get strip endpoints from TGeoNavigator
  Int_t statnb = fDetectorID/10000;
  Int_t orientationnb = (fDetectorID-statnb*10000)/1000;  //1=vertical, 0=horizontal
  if (orientationnb > 1) {
     std::cout << "MuonTagger::StripEndPoints, not a sensitive volume "<<fDetectorID<<std::endl;              
     return;
  }
  TString stat="VMuonBox_1/VSensitive";stat+=+statnb;stat+="_";stat+=statnb;
  TString striptype;
  if (orientationnb == 0) { 
    striptype = "Hstrip_";
    if (fDetectorID%1000==116 || fDetectorID%1000==1){striptype = "Hstrip_ext_";}
  }
  if (orientationnb == 1) { 
    striptype = "Vstrip_";
    if (fDetectorID%1000==184){striptype = "Vstrip_L_";}
    if (fDetectorID%1000==1){striptype = "Vstrip_R_";}
  }
  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  TString path = "";path+="/";path+=stat;path+="/"+striptype;path+=fDetectorID;
  Bool_t rc = nav->cd(path);
  if (not rc){
       std::cout << "MuonTagger::StripEndPoints, TGeoNavigator failed "<<path<<std::endl; 
       return;
  }  
  TGeoNode* W = nav->GetCurrentNode();
  TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());
  Double_t top[3] = {S->GetDX(),S->GetDY(),S->GetDZ()};
  Double_t bot[3] = {-S->GetDX(),-S->GetDY(),-S->GetDZ()};
  Double_t Gtop[3],Gbot[3];
  nav->LocalToMaster(top, Gtop);
  nav->LocalToMaster(bot, Gbot);
  if (orientationnb ==0) {
     vtop.SetXYZ(Gbot[0],(Gbot[1]+Gtop[1])/2.,(Gtop[2]+Gbot[2])/2.);    
     vbot.SetXYZ(Gtop[0],(Gbot[1]+Gtop[1])/2.,(Gtop[2]+Gbot[2])/2.);      
  }     
  if (orientationnb ==1) {
     vtop.SetXYZ((Gtop[0]+Gbot[0])/2.,Gbot[1],(Gtop[2]+Gbot[2])/2.);    
     vbot.SetXYZ((Gtop[0]+Gbot[0])/2.,Gtop[1],(Gtop[2]+Gbot[2])/2.);      
  }       
}

ClassImp(MuonTagger)








