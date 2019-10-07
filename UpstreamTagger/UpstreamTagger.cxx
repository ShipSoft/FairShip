// RPC Timing Detector
// 15/02/2019
// celso.franco@cern.ch

#include "UpstreamTagger.h"
#include "UpstreamTaggerPoint.h"
#include "UpstreamTaggerHit.h"

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
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TMath.h" 
#include "TParticle.h" 
#include "TVector3.h"

#include <iostream>
#include <sstream>
using std::cout;
using std::endl;


UpstreamTagger::UpstreamTagger()
  : FairDetector("UpstreamTagger", kTRUE, kUpstreamTagger),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    //
    det_zPos(0),     

    det_xGlassPos(0),    
    det_yGlassPos(0),    
    det_zGlassPos(0), 

    det_xGlassBorderPos(0),    
    det_yGlassBorderPos(0),    
    det_zGlassBorderPos(0), 

    det_xPMMAPos(0),     
    det_yPMMAPos(0),     
    det_zPMMAPos(0),     

    det_dxPMMAPos(0),     
    det_dyPMMAPos(0),     
    det_dzPMMAPos(0),     

    det_xFreonSF6Pos(0),    
    det_yFreonSF6Pos(0),    
    det_zFreonSF6Pos(0),    

    det_xFR4Pos(0),    
    det_yFR4Pos(0),    
    det_zFR4Pos(0),    

    det_xAlPos(0),     
    det_yAlPos(0),     
    det_zAlPos(0),     

    det_dxAlPos(0),    
    det_dyAlPos(0),    
    det_dzAlPos(0),    

    det_xAirPos(0),    
    det_yAirPos(0),    
    det_zAirPos(0),

    det_xStripPos(0),    
    det_yStripPos(0),    
    det_zStripPos(0),  
    
    //
    UpstreamTagger_fulldet(0),
  //
    fUpstreamTaggerPointCollection(new TClonesArray("UpstreamTaggerPoint"))
{
}

UpstreamTagger::UpstreamTagger(const char* name, Bool_t active)
  : FairDetector(name, active, kUpstreamTagger),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    //
    det_zPos(0),     

    det_xGlassPos(0),    
    det_yGlassPos(0),    
    det_zGlassPos(0),    

    det_xGlassBorderPos(0),    
    det_yGlassBorderPos(0),    
    det_zGlassBorderPos(0), 

    det_xPMMAPos(0),     
    det_yPMMAPos(0),     
    det_zPMMAPos(0),     

    det_dxPMMAPos(0),     
    det_dyPMMAPos(0),     
    det_dzPMMAPos(0),     

    det_xFreonSF6Pos(0),    
    det_yFreonSF6Pos(0),    
    det_zFreonSF6Pos(0),    

    det_xFR4Pos(0),    
    det_yFR4Pos(0),    
    det_zFR4Pos(0),    

    det_xAlPos(0),     
    det_yAlPos(0),     
    det_zAlPos(0),     

    det_dxAlPos(0),    
    det_dyAlPos(0),    
    det_dzAlPos(0),

    det_xAirPos(0),    
    det_yAirPos(0),    
    det_zAirPos(0),

    det_xStripPos(0),    
    det_yStripPos(0),    
    det_zStripPos(0),  

    //
    UpstreamTagger_fulldet(0),
        //
    fUpstreamTaggerPointCollection(new TClonesArray("UpstreamTaggerPoint"))
{
}


void UpstreamTagger::Initialize()
{
  FairDetector::Initialize();
}


UpstreamTagger::~UpstreamTagger()
{
  if (fUpstreamTaggerPointCollection) {
    fUpstreamTaggerPointCollection->Delete();
    delete fUpstreamTaggerPointCollection;
  }
}



Int_t UpstreamTagger::InitMedium(const char* name)
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
  
  return 0;
}



Bool_t  UpstreamTagger::ProcessHits(FairVolume* vol)
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

  // Create vetoPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    if (fELoss == 0. ) { return kFALSE; }

    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();

    Int_t uniqueId;
    gMC->CurrentVolID(uniqueId);
    if (uniqueId>1000000) //Solid scintillator case
    {
      Int_t vcpy;
      gMC->CurrentVolOffID(1, vcpy);
      if (vcpy==5) uniqueId+=4; //Copy of half
    }

    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;

    //cout << uniqueId << " :(" << xmean << ", " << ymean << ", " << zmean << "): " << gMC->CurrentVolName() << endl;

    AddHit(fTrackID, uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),
	   TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );

    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kUpstreamTagger);
  }
  
  return kTRUE;
}



void UpstreamTagger::EndOfEvent()
{
  fUpstreamTaggerPointCollection->Clear();
}



void UpstreamTagger::Register()
{

  /** This will create a branch in the output tree called
      UpstreamTaggerPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("UpstreamTaggerPoint", "UpstreamTagger",
                                        fUpstreamTaggerPointCollection, kTRUE);
}



TClonesArray* UpstreamTagger::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fUpstreamTaggerPointCollection; }
  else { return NULL; }
}



void UpstreamTagger::Reset()
{
  fUpstreamTaggerPointCollection->Clear();
}



void UpstreamTagger::ConstructGeometry()
{
  TGeoVolume *top = gGeoManager->GetTopVolume();

  //////////////////////////////////////////////////////

  InitMedium("aluminium");  
  TGeoMedium *rpc_al =gGeoManager->GetMedium("aluminium"); 

  InitMedium("TimeRpc_gas");  
  TGeoMedium *rpc_gas =gGeoManager->GetMedium("TimeRpc_gas"); 

  InitMedium("air");  
  TGeoMedium *rpc_air =gGeoManager->GetMedium("air"); 

  InitMedium("copper");
  TGeoMedium *rpc_strip =gGeoManager->GetMedium("copper"); 
    
  InitMedium("TimeRpc_glass");  
  TGeoMedium *rpc_glass =gGeoManager->GetMedium("TimeRpc_glass");

  InitMedium("TimeRpc_pmma");  
  TGeoMedium *rpc_pmma =gGeoManager->GetMedium("TimeRpc_pmma");

  InitMedium("TimeRpc_FR4");  
  TGeoMedium *rpc_FR4 =gGeoManager->GetMedium("TimeRpc_FR4");

  ///////////////////////////////////////////////////////

  TGeoVolume *vol_al1 = gGeoManager->MakeBox("Al1", rpc_al, (det_xAlPos + (2*det_dxAlPos))/2.0, (det_yAlPos + (2*det_dyAlPos))/2.0, det_dzAlPos/2.0);
  vol_al1->SetLineColor(kBlue);//Gray);

  TGeoVolume *vol_al2 = gGeoManager->MakeBox("Al2", rpc_al, (det_xAlPos + (2*det_dxAlPos))/2.0, det_dyAlPos/2.0, det_zAlPos/2.0);
  vol_al2->SetLineColor(kRed);//Gray);

  TGeoVolume *vol_al3 = gGeoManager->MakeBox("Al3", rpc_al, (det_dxAlPos)/2.0, (det_yAlPos + (2*det_dyAlPos))/2.0, det_zAlPos/2.0);
  vol_al3->SetLineColor(kRed);//);

  TGeoVolume *vol_strip = gGeoManager->MakeBox("strip", rpc_strip, (det_xStripPos)/2.0, (det_yStripPos)/2.0, det_zStripPos/2.0);
  vol_strip->SetLineColor(42);
  
  TGeoVolume *vol_pmma1 = gGeoManager->MakeBox("pmma1", rpc_pmma, (det_xPMMAPos+(2*det_dxPMMAPos))/2.0, (det_yPMMAPos + (2*det_dyPMMAPos))/2.0, det_dzPMMAPos/2.0);
  vol_pmma1->SetLineColor(kYellow);

  TGeoVolume *vol_pmma2 = gGeoManager->MakeBox("pmma2", rpc_pmma, (det_xPMMAPos+(2*det_dxPMMAPos))/2.0, (det_dyPMMAPos)/2.0, det_zPMMAPos/2.0);
  vol_pmma2->SetLineColor(kYellow);

  TGeoVolume *vol_pmma3 = gGeoManager->MakeBox("pmma3", rpc_pmma, (det_dxPMMAPos)/2.0, (det_yPMMAPos + (2*det_dyPMMAPos))/2.0, det_zPMMAPos/2.0);
  vol_pmma3->SetLineColor(kYellow);

  TGeoVolume *vol_glass = gGeoManager->MakeBox("glass_upstreamtagger", rpc_glass, det_xGlassPos/2.0, det_yGlassPos/2.0, det_zGlassPos/2.0);
  vol_glass->SetLineColor(kBlue);
  AddSensitiveVolume(vol_glass);

  TGeoVolume *vol_glass_border = gGeoManager->MakeBox("glassB", rpc_glass, (det_xGlassPos + (det_xGlassBorderPos*2.0))/2.0, det_yGlassBorderPos/2.0, det_zGlassBorderPos/2.0);
  vol_glass_border->SetLineColor(kRed);

  TGeoVolume *vol_glass_border1 = gGeoManager->MakeBox("glassB1", rpc_glass, det_xGlassBorderPos/2.0, det_yGlassPos/2.0, det_zGlassBorderPos/2.0);
  vol_glass_border1->SetLineColor(kRed);

  TGeoVolume *vol_FR4 = gGeoManager->MakeBox("FR4", rpc_FR4, det_xFR4Pos/2.0, det_yFR4Pos/2.0, det_zFR4Pos/2.0);
  vol_FR4->SetLineColor(kBlack);

  TGeoVolume *vol_air = gGeoManager->MakeBox("air", rpc_air, (det_xPMMAPos + (2*det_dxPMMAPos))/2.0, det_yAirPos/2.0, det_zAirPos/2.0);
  vol_air->SetLineColor(kWhite);

  TGeoVolume *vol_FrSF6 = gGeoManager->MakeBox("gas1", rpc_gas, det_xFreonSF6Pos/2.0, det_yFreonSF6Pos/2.0, det_zFreonSF6Pos/2.0);
  vol_FrSF6->SetLineColor(kGreen);
  
  TGeoVolume *vol_FrSF6_2 = gGeoManager->MakeBox("gas2", rpc_gas, det_xPMMAPos/2.0, det_yFreonSF6Pos_2/2.0, det_zFreonSF6Pos_2/2.0);
  vol_FrSF6_2->SetLineColor(kGreen);

  TGeoVolume *vol_FrSF6_3 = gGeoManager->MakeBox("gas3", rpc_gas, det_xFreonSF6Pos_2/2.0, (det_yPMMAPos/2.0 - (2*det_yFreonSF6Pos_2)/2.0), det_zFreonSF6Pos_2/2.0);
  vol_FrSF6_2->SetLineColor(kGreen);

    
  ////////////////////////////////////////////////////////////////////

  InitMedium("vacuum");  
  TGeoMedium *Vacuum_box =gGeoManager->GetMedium("vacuum");
  //double xbox=117; double ybox = 175.4; double zbox = 2.3503;
  double xbox=215.4; double ybox = 108; double zbox = 1.3503;
  TGeoVolume *Rpc_module_upstream = gGeoManager->MakeBox("UpstreamTagger",Vacuum_box, xbox/2.0, ybox/2.0, zbox/2.0);
  Rpc_module_upstream->SetLineColor(kRed);

  //RPC Module_Upstream
  Rpc_module_upstream->AddNode(vol_al1, 145, new TGeoTranslation(0, 0, (-(det_zAlPos/2.0) - (det_dzAlPos/2.0)) ));
  Rpc_module_upstream->AddNode(vol_al2, 146, new TGeoTranslation(0, ((-det_yAlPos/2.0) - (det_dyAlPos/2.0)), 0));	  
  Rpc_module_upstream->AddNode(vol_al2, 147, new TGeoTranslation(0, ((det_yAlPos/2.0) + (det_dyAlPos/2.0)), 0));
  Rpc_module_upstream->AddNode(vol_al3, 148, new TGeoTranslation(((-det_xAlPos/2.0) - (det_dxAlPos/2.0)), 0, 0));	  
  Rpc_module_upstream->AddNode(vol_al3, 149, new TGeoTranslation(((det_xAlPos/2.0) + (det_dxAlPos/2.0)), 0, 0));
  Rpc_module_upstream->AddNode(vol_al1, 150, new TGeoTranslation(0, 0, ((det_zAlPos/2.0) + (det_dzAlPos/2.0)) ));
  
  Rpc_module_upstream->AddNode(vol_pmma1, 151, new TGeoTranslation(0, 0, -((det_zAlPos/2.0) - (det_dzPMMAPos/2.0))));
  Rpc_module_upstream->AddNode(vol_pmma2, 152, new TGeoTranslation(0, ((-det_yPMMAPos/2.0) - (det_dyPMMAPos/2.0)), 0 - (det_zFR4Pos + det_zStripPos)/2.0 ));   
  Rpc_module_upstream->AddNode(vol_pmma2, 153, new TGeoTranslation(0, ((det_yPMMAPos/2.0) + (det_dyPMMAPos/2.0)),0 - (det_zFR4Pos + det_zStripPos)/2.0  ));
  Rpc_module_upstream->AddNode(vol_pmma3, 154, new TGeoTranslation(((-det_xPMMAPos/2.0) - (det_dxPMMAPos/2.0)), 0, 0 - (det_zFR4Pos + det_zStripPos)/2.0 ));   
  Rpc_module_upstream->AddNode(vol_pmma3, 155, new TGeoTranslation(((det_xPMMAPos/2.0) + (det_dxPMMAPos/2.0)), 0, 0 - (det_zFR4Pos + det_zStripPos)/2.0 ));   
  Rpc_module_upstream->AddNode(vol_pmma1, 156, new TGeoTranslation(0, 0, -(det_zAlPos/2.0) + det_dzPMMAPos + det_zPMMAPos + (det_dzPMMAPos/2.0) ));
      
  Rpc_module_upstream->AddNode(vol_glass_border, 157, new TGeoTranslation(0, ((det_yGlassPos/2.0) + (det_yGlassBorderPos/2.0)), ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border, 158, new TGeoTranslation(0, (-(det_yGlassPos/2.0) - (det_yGlassBorderPos/2.0)), ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border1, 159, new TGeoTranslation(((det_xGlassPos/2.0) + (det_xGlassBorderPos/2.0)), 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border1, 160, new TGeoTranslation((-(det_xGlassPos/2.0) - (det_xGlassBorderPos/2.0)), 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos/2.0))));

  Rpc_module_upstream->AddNode(vol_glass_border, 161, new TGeoTranslation(0, ((det_yGlassPos/2.0) + (det_yGlassBorderPos/2.0)), ((det_zAlPos/2.0) - det_dzPMMAPos - det_zGlassPos -  det_zFreonSF6Pos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border, 162, new TGeoTranslation(0, (-(det_yGlassPos/2.0) - (det_yGlassBorderPos/2.0)),  ((det_zAlPos/2.0) - det_dzPMMAPos - det_zGlassPos -  det_zFreonSF6Pos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border1, 163, new TGeoTranslation(((det_xGlassPos/2.0) + (det_xGlassBorderPos/2.0)), 0,  ((det_zAlPos/2.0) - det_dzPMMAPos - det_zGlassPos -  det_zFreonSF6Pos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border1, 164, new TGeoTranslation((-(det_xGlassPos/2.0) - (det_xGlassBorderPos/2.0)), 0,  ((det_zAlPos/2.0) - det_dzPMMAPos - det_zGlassPos -  det_zFreonSF6Pos - (det_zGlassPos/2.0))));
  
  Rpc_module_upstream->AddNode(vol_glass_border, 165, new TGeoTranslation(0, ((det_yGlassPos/2.0) + (det_yGlassBorderPos/2.0)), ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos*2.0) -  (det_zFreonSF6Pos*2.0) - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border, 166, new TGeoTranslation(0, (-(det_yGlassPos/2.0) - (det_yGlassBorderPos/2.0)), ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos*2.0) -  (det_zFreonSF6Pos*2.0) - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border1, 167, new TGeoTranslation(((det_xGlassPos/2.0) + (det_xGlassBorderPos/2.0)), 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos*2.0) -  (det_zFreonSF6Pos*2.0) - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass_border1, 168, new TGeoTranslation((-(det_xGlassPos/2.0) - (det_xGlassBorderPos/2.0)), 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos*2.0) -  (det_zFreonSF6Pos*2.0) - (det_zGlassPos/2.0))));

  Rpc_module_upstream->AddNode(vol_glass, 169, new TGeoTranslation(0, 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass, 170, new TGeoTranslation(0, 0, ((det_zAlPos/2.0) - det_dzPMMAPos - det_zGlassPos -  det_zFreonSF6Pos - (det_zGlassPos/2.0))));
  Rpc_module_upstream->AddNode(vol_glass, 171, new TGeoTranslation(0, 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos*2.0) -  (det_zFreonSF6Pos*2.0) - (det_zGlassPos/2.0))));
  
  Rpc_module_upstream->AddNode(vol_FrSF6, 172, new TGeoTranslation(0, 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos*1.0)  -  (det_zFreonSF6Pos/2.0))));
  Rpc_module_upstream->AddNode(vol_FrSF6, 173, new TGeoTranslation(0, 0, ((det_zAlPos/2.0) - det_dzPMMAPos - (det_zGlassPos*2.0)  - (det_zFreonSF6Pos*1.0) - (det_zFreonSF6Pos/2.0))));
  
  Rpc_module_upstream->AddNode(vol_FrSF6_2, 174, new TGeoTranslation(0, ((-det_yGlassPos/2.0) - det_yGlassBorderPos - (det_yFreonSF6Pos_2/2.0)), (-(det_zAlPos/2.0) + (det_dzPMMAPos) + (det_zFreonSF6Pos_2/2.0))));
  Rpc_module_upstream->AddNode(vol_FrSF6_2, 175, new TGeoTranslation(0, ((det_yGlassPos/2.0) + det_yGlassBorderPos + (det_yFreonSF6Pos_2/2.0)), (-(det_zAlPos/2.0) + (det_dzPMMAPos) + (det_zFreonSF6Pos_2/2.0))));
  Rpc_module_upstream->AddNode(vol_FrSF6_3, 176, new TGeoTranslation(((det_xGlassPos/2.0) + det_xGlassBorderPos + (det_xFreonSF6Pos_2/2.0)), 0, (-(det_zAlPos/2.0) + (det_dzPMMAPos) + (det_zFreonSF6Pos_2/2.0))));
  Rpc_module_upstream->AddNode(vol_FrSF6_3, 177, new TGeoTranslation(((-det_xGlassPos/2.0) - det_xGlassBorderPos - (det_xFreonSF6Pos_2/2.0)), 0, (-(det_zAlPos/2.0) + (det_dzPMMAPos) + (det_zFreonSF6Pos_2/2.0))));
  
  Rpc_module_upstream->AddNode(vol_FR4, 178, new TGeoTranslation(0, 0, -(det_zAlPos/2.0) + det_dzPMMAPos + det_zPMMAPos + det_dzPMMAPos + det_zFR4Pos/2.0));
  		     
  Rpc_module_upstream->AddNode(vol_air, 179, new TGeoTranslation(0, ((-det_yAlPos/2.0) + (det_yAirPos/2.0)), 0));
  Rpc_module_upstream->AddNode(vol_air, 180, new TGeoTranslation(0, ((det_yAlPos/2.0) - (det_yAirPos/2.0)), 0));

  Int_t interval = 0;
 
  //Add 32 copper strips to the Rpc module
  for(int i = 181; i < 213; i++){

    Rpc_module_upstream->AddNode(vol_strip, i, new TGeoTranslation(0, (-det_yGlassPos/2.0) - det_yGlassBorderPos + 1.45 + (interval*det_yStripPos) + (interval*0.1) + ((det_yStripPos/2.0)),  -(det_zAlPos/2.0) + det_dzPMMAPos + det_zPMMAPos + det_dzPMMAPos + det_zFR4Pos + (det_zStripPos/2.0) ));
    interval++;
  }
  

  /////////////////////////////////////////////////////////////////// 
  
  //UpstreamTagger_fulldet = new TGeoVolumeAssembly("Upstream_Tagger");
  UpstreamTagger_fulldet = gGeoManager->MakeBox("Upstream_Tagger", Vacuum_box, xbox_fulldet/2.0, ybox_fulldet/2.0, zbox_fulldet/2.0);
  UpstreamTagger_fulldet->SetLineColor(kWhite);
  
 
  module[0][0] = 0; module[0][1] = 0; module[0][2] = 0;

  //First Layer of full Rpc detector covering 2.17 x 4.91 meters
  module[1][0] = 0; module[1][1] = ((ybox_fulldet/2.0) - (((det_yGlassBorderPos*2.0) + det_yGlassPos)/2.0));  module[1][2] = (-(zbox_fulldet/2.0) + (det_zAlPos/2.0) + det_dzAlPos);
  module[2][0] = 0; module[2][1] = 0; module[2][2] = (-(zbox_fulldet/2.0) + (det_zAlPos/2.0) + det_dzAlPos) ;
  module[3][0] = 0; module[3][1] = -((ybox_fulldet/2.0) - (((det_yGlassBorderPos*2.0) + det_yGlassPos)/2.0)); module[3][2] = (-(zbox_fulldet/2.0) + (det_zAlPos/2.0) + det_dzAlPos) ;
   
  //Second Layer of full Rpc detector covering 2.17 x 4.91 meters

  module[4][0] = 0; module[4][1] = ((ybox_fulldet/2.0) - (((det_yGlassBorderPos*2.0) + det_yGlassPos)) - (((det_yGlassBorderPos*2.0) + det_yGlassPos)/2.0) + extra_y); module[4][2] = (-(zbox_fulldet/2.0) + det_zAlPos + det_dzAlPos*3.0 + z_space_layers + (det_zAlPos/2.0)); 
  module[5][0] = 0; module[5][1] = -((ybox_fulldet/2.0) - (((det_yGlassBorderPos*2.0) + det_yGlassPos)) - (((det_yGlassBorderPos*2.0) + det_yGlassPos)/2.0) + extra_y);  module[5][2] = (-(zbox_fulldet/2.0) + det_zAlPos + det_dzAlPos*3.0 + z_space_layers + (det_zAlPos/2.0));


  //First Layer of full Rpc detector1 covering 2.17 x 4.91 meters
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 1, new TGeoTranslation(module[1][0], module[1][1], module[1][2]));
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 2, new TGeoTranslation(module[2][0], module[2][1], module[2][2])); 
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 3, new TGeoTranslation(module[3][0], module[3][1], module[3][2]));

  //Second Layer of full Rpc detector1 covering 2.17 x 4.91 meters
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 4, new TGeoTranslation(module[4][0], module[4][1], module[4][2])); 
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 5, new TGeoTranslation(module[5][0], module[5][1], module[5][2]));

  //First Layer of full Rpc detector1 covering 2.17 x 4.91 meters
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 6, new TGeoTranslation(module[1][0], module[1][1], -module[4][2]));
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 7, new TGeoTranslation(module[2][0], module[2][1], -module[4][2])); 
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 8, new TGeoTranslation(module[3][0], module[3][1], -module[4][2]));

  //Second Layer of full Rpc detector1 covering 2.17 x 4.91 meters
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 9, new TGeoTranslation(module[4][0], module[4][1], -module[1][2])); 
  UpstreamTagger_fulldet->AddNode(Rpc_module_upstream, 10, new TGeoTranslation(module[5][0], module[5][1], -module[1][2]));
  
  top->AddNode(UpstreamTagger_fulldet, 1, new TGeoTranslation(0.0, 0.0, det_zPos));
  
  cout << " Z Position (Upstream Tagger1) " << det_zPos << endl;//" Z Position (Upstream Tagger2) " << " " << det_zPos + 5 + det_zAlPos + (2*det_dzAlPos) << endl;
  //////////////////////////////////////////////////////////////////

  return;
}



UpstreamTaggerPoint* UpstreamTagger::AddHit(Int_t trackID, Int_t detID,
			TVector3 pos, TVector3 mom,
			Double_t time, Double_t length,
			Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fUpstreamTaggerPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "veto hit called "<< pos.z()<<endl;
  return new(clref[size]) UpstreamTaggerPoint(trackID, detID, pos, mom,
		         time, length, eLoss, pdgCode,Lpos,Lmom);
}


ClassImp(UpstreamTagger)
