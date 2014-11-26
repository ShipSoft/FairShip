// First version of the strawtracker geometry, based on NA62 straws
// 7/10/2015
// E. van Herwijnen eric.van.herwijnen@cern.ch
// Also contains (for the moment) the veto station

#include "strawtubes.h"
#include "strawtubesPoint.h"

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
using std::cout;
using std::endl;

strawtubes::strawtubes()
  : FairDetector("strawtubes", kTRUE, kStraw),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fstrawtubesPointCollection(new TClonesArray("strawtubesPoint"))
{
}

strawtubes::strawtubes(const char* name, Bool_t active)
  : FairDetector(name, active, kStraw),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    // these values are initialized in geometry/geometry_config.py, kept here for convenience
    //fT0z(-2390.),                    //!  z-position of veto station
    //fT1z(1520.),                     //!  z-position of tracking station 1
    //fT2z(1720.),                     //!  z-position of tracking station 2
    //fT3z(2160.),                     //!  z-position of tracking station 3 (avoid overlap with magnet)
    //fT4z(2380.),                     //!  z-position of tracking station 4 (avoid overlap with ecal)

    //fStraw_length(250.),             //!  Length (y) of a straw
    //fInner_Straw_diameter(0.94),     //!  Inner Straw diameter
    //fOuter_Straw_diameter(0.98),     //!  Outer Straw diameter
    //fStraw_pitch(1.76),              //!  Distance (x) between straws in one layer
    //fDeltaz_layer12(1.1),            //!  Distance (z) between layer 1&2
    //fDeltaz_plane12(2.6),            //!  Distance (z) between plane 1&2
    //fOffset_layer12(fStraw_pitch/2), //!  Offset (x) between straws of layer1&2
    //fOffset_plane12(fStraw_pitch/4), //!  Offset (x) between straws of plane1&2
    //fStraws_per_layer(284),          //!  Number of straws in one layer
    //fView_angle(5),                  //!  Stereo angle of layers in a view
    //fWire_thickness(0.003),          //!  Thickness of the wire
    //fDeltaz_view(10.),               //!  Distance (z) between views
    //fVacbox_x(550.),                 //!  x of station vacuum box; x will become y after rotation
    //fVacbox_y(300.),                 //!  y of station vacuum box
    fstrawtubesPointCollection(new TClonesArray("strawtubesPoint"))
{
}

strawtubes::~strawtubes()
{
  if (fstrawtubesPointCollection) {
    fstrawtubesPointCollection->Delete();
    delete fstrawtubesPointCollection;
  }
}

void strawtubes::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  vetoGeoPar* par=(vetoGeoPar*)(rtdb->getContainer("vetoGeoPar"));
}

// -----   Private method InitMedium
Int_t strawtubes::InitMedium(const char* name)
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

Bool_t  strawtubes::ProcessHits(FairVolume* vol)
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

  // Create strawtubesPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    if (fELoss == 0. ) { return kFALSE; }
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    Int_t straw_uniqueId;
    Int_t VoIid = gMC->CurrentVolID(straw_uniqueId);
    if (fVolumeID == straw_uniqueId) {
        //std::cout << pdgCode<< " same volume again ? "<< straw_uniqueId << " exit:" << gMC->IsTrackExiting() << " stop:" << gMC->IsTrackStop() << " disappeared:" << gMC->IsTrackDisappeared()<< std::endl;
         return kFALSE; }
    fVolumeID = straw_uniqueId;
     // # d = |pq . u x v|/|u x v|
    TVector3 bot,top;
    StrawEndPoints(straw_uniqueId,bot,top);
    TLorentzVector Pos; 
    gMC->TrackPosition(Pos); 
    Double_t xmean = (fPos.X()+Pos.X())/2. ;      
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
    TVector3 pq = TVector3(top.x()-xmean,top.y()-ymean,top.z()-zmean );
    TVector3 u  = TVector3(bot.x()-top.x(),bot.y()-top.y(),bot.z()-top.z() ); 
    TVector3 v  = TVector3(fMom.Px(),fMom.Py(), fMom.Pz() );
    TVector3 uCrossv = u.Cross(v);
    Double_t dist2Wire  = fabs(pq.Dot(uCrossv))/(uCrossv.Mag()+1E-8);
    Double_t deltaTrackLength = gMC->TrackLength() - fLength; 
    AddHit(fTrackID, straw_uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, deltaTrackLength,
           fELoss,pdgCode,dist2Wire);
    if (dist2Wire==0){
     std::cout << "addhit " << dist2Wire<< " pdgcode" << pdgCode<< " dot prod " << pq.Dot(uCrossv)<< std::endl;
     std::cout << " exit:" << gMC->IsTrackExiting() << " stop:" << gMC->IsTrackStop() << " disappeared:" << gMC->IsTrackDisappeared()<< std::endl;
     pq.Print();
     u.Print();
     v.Print();
     uCrossv.Print();
    }
    // Increment number of strawtubes det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kStraw);
  }
  return kTRUE;
}

void strawtubes::EndOfEvent()
{

  fstrawtubesPointCollection->Clear();

}



void strawtubes::Register()
{

  /** This will create a branch in the output tree called
      strawtubesPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("strawtubesPoint", "strawtubes",
                                        fstrawtubesPointCollection, kTRUE);

}


TClonesArray* strawtubes::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fstrawtubesPointCollection; }
  else { return NULL; }
}

void strawtubes::Reset()
{
  fstrawtubesPointCollection->Clear();
}
void strawtubes::SetZpositions(Double32_t z0, Double32_t z1, Double32_t z2, Double32_t z3, Double32_t z4)
{
     fT0z = z0;                                                 //!  z-position of veto station
     fT1z = z1;                                                 //!  z-position of tracking station 1
     fT2z = z2;                                                 //!  z-position of tracking station 2
     fT3z = z3;                                                 //!  z-position of tracking station 3
     fT4z = z4;                                                 //!  z-position of tracking station 4
}

void strawtubes::SetStrawLength(Double32_t strawlength)
{
     fStraw_length = strawlength;                               //!  Length (y) of a straw
}

void strawtubes::SetInnerStrawDiameter(Double32_t innerstrawdiameter)
{
     fInner_Straw_diameter = innerstrawdiameter;                //!  Inner Straw diameter
}

void strawtubes::SetOuterStrawDiameter(Double32_t outerstrawdiameter)
{
     fOuter_Straw_diameter = outerstrawdiameter;                //!  Outer Straw diameter
}


void strawtubes::SetStrawPitch(Double32_t strawpitch)
{
     fStraw_pitch = strawpitch;                                 //!  Distance (x) between straws in one layer
     fOffset_layer12 = strawpitch/2;
     fOffset_plane12 = strawpitch/4;
}

void strawtubes::SetDeltazLayer(Double32_t deltazlayer)
{
     fDeltaz_layer12 = deltazlayer;                              //! Distance (z) between layer 1&2
}

void strawtubes::SetDeltazPlane(Double32_t deltazplane)
{
     fDeltaz_plane12 = deltazplane;                              //! Distance (z) between plane 1&2
}

void strawtubes::SetStrawsPerLayer(Int_t strawsperlayer)
{
     fStraws_per_layer = strawsperlayer;                         //! number of straws in one layer
}

void strawtubes::SetStereoAngle(Int_t stereoangle)
{
     fView_angle = stereoangle;                                  //! Stereo angle of planes in a view
     fcosphi=cos(TMath::Pi()*fView_angle/180.);
     fsinphi=sin(TMath::Pi()*fView_angle/180.);
}

void strawtubes::SetWireThickness(Double32_t wirethickness)
{
     fWire_thickness = wirethickness;                            //! Thickness of the wire
}

void strawtubes::SetDeltazView(Double32_t deltazview)
{
     fDeltaz_view = deltazview;                            //! Distance (z) between views
}

void strawtubes::SetVacBox_x(Double32_t vacbox_x)
{
     fVacBox_x = vacbox_x;                               //! x size of station vacuum box
}

void strawtubes::SetVacBox_y(Double32_t vacbox_y)
{
     fVacBox_y = vacbox_y;                               //! y size of station vacuum box
}

void strawtubes::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */

    TGeoVolume *top               = gGeoManager->GetTopVolume();
    InitMedium("air");
    TGeoMedium *air               = gGeoManager->GetMedium("air");
    InitMedium("ShipSens");
    TGeoMedium *Se                = gGeoManager->GetMedium("ShipSens");
    InitMedium("aluminium");
    TGeoMedium *Al                = gGeoManager->GetMedium("aluminium");
    InitMedium("mylar");
    TGeoMedium *mylar             = gGeoManager->GetMedium("mylar");
    InitMedium("STTmix9010_2bar");
    TGeoMedium *sttmix9010_2bar   = gGeoManager->GetMedium("STTmix9010_2bar");
    InitMedium("tungsten");
    TGeoMedium *tungsten          = gGeoManager->GetMedium("tungsten");
    InitMedium("vacuum");
    TGeoMedium *med          = gGeoManager->GetMedium("vacuum");

    gGeoManager->SetVisLevel(4);
    gGeoManager->SetTopVisible();
    
    //epsilon to avoid overlapping volumes
    Double_t eps=0.1;
    //width of frame
    Double_t framewidth = 40.;
    //width of view
    Double_t viewwidth = fDeltaz_view-eps;
    //width of plane
    Double_t planewidth = fOuter_Straw_diameter+fDeltaz_layer12-eps;
    //width of layer
    Double_t layerwidth = fOuter_Straw_diameter;

    Double_t rmin, rmax, dx, dy, dz, z, density,a,w;
    Double_t par[20];
    Int_t nel,numed,isvol,ifield;
    Double_t radl, absl, TStationz;
    
    Double_t yDim =  (fStraws_per_layer+1) * fStraw_pitch /2. ; // put everything inside vacbox
    //arguments of box are half-lengths; 
    TGeoBBox *detbox1 = new TGeoBBox("detbox1", fStraw_length+5.,  yDim+5., fDeltaz_view/2.);
    TGeoBBox *detbox2 = new TGeoBBox("detbox2", fStraw_length+eps, yDim+eps, fDeltaz_view/2.+eps);

    //the station sits inside a vacuum box
    TGeoBBox *vetovacbox = new TGeoBBox("Vetovacbox", fVacBox_x, fVacBox_y, fDeltaz_view );
    TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");
    
    // Volume: straw
    rmin = fInner_Straw_diameter/2.;
    rmax = fOuter_Straw_diameter/2.;
    //third argument is halflength of tube
    TGeoTube *straw_tube = new TGeoTube("straw",rmin,rmax,fStraw_length-4.*eps);
    TGeoVolume *straw = new TGeoVolume("straw",straw_tube, mylar);
    straw->SetLineColor(4);

    straw->SetVisibility(kTRUE);
	       	
    // Volume: gas
    rmin = fWire_thickness/2.+eps;
    rmax = fInner_Straw_diameter/2.-eps;
    TGeoTube *gas_tube = new TGeoTube("gas",rmin,rmax,fStraw_length-6.*eps);
    TGeoVolume *gas = new TGeoVolume("gas",gas_tube, sttmix9010_2bar);
    gas->SetLineColor(5);    //only the gas is sensitive
    AddSensitiveVolume(gas);

    // Volume: wire
    rmin=0.;
    rmax = fWire_thickness/2.;
    TGeoTube *wire_tube = new TGeoTube("wire",rmin,rmax,fStraw_length-8.*eps);
    TGeoVolume *wire = new TGeoVolume("wire",wire_tube, tungsten);
    wire->SetLineColor(6);   
    Int_t statnb;
    statnb=5;
    // statnb = station number. 1,2,3,4 tracking stations, 5 veto station
    TGeoVolume *vetovac = new TGeoVolume("Veto", vetovacbox, med);

    top->AddNode(vetovac, statnb, new TGeoTranslation(0,0,fT0z));
    //vetovac->SetVisDaughters(kTRUE);
    //vetovac->SetTransparency(80);

    //Veto station

    //vnb=view number; pnb=plane number; lnb=layer number; snb=straw number
    TString nmveto = "Veto"; 	
    TStationz=fT0z;
    for (Int_t vnb=0; vnb<2; vnb++) {
      //view loop
      TString nmview;
      Double_t angle;
      TGeoRotation r5;	
      TGeoTranslation t5; 			
      switch (vnb) {
	   case 0:
	      angle=0.;
	      nmview = nmveto+"_x";
	      break;
	   case 1:
	      angle=fView_angle;
	      nmview = nmveto+"_u";
	      break;
	   default:
	      angle=0.;
	      nmview = nmveto+"_x";
      }	

      TGeoVolume *viewframe = new TGeoVolume(nmview, detcomp1, Al);
      //z-translate the viewframe from station z pos
      t5.SetTranslation(0, 0,(vnb-1./2.)*fDeltaz_view);
      //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)	
      r5.SetAngles(angle,0,0);
      TGeoCombiTrans c5(t5, r5);
      TGeoHMatrix *h5 = new TGeoHMatrix(c5);	
      vetovac->AddNode(viewframe, statnb*10000000+vnb*1000000,h5);
      viewframe->SetLineColor(kRed);

      TGeoTranslation t5p;
	 	
      for (Int_t pnb=0; pnb<2; pnb++) {
	 //plane loop
         TString nmplane = nmview+"_plane_"; nmplane += pnb;
	 //width of the planes: z distance between layers + outer straw diameter
	 TGeoBBox *plane = new TGeoBBox("plane box", fStraw_length+eps/2, yDim+eps/2, planewidth/2.+eps/2);
         TGeoVolume *planebox = new TGeoVolume(nmplane, plane, med);
	 //the planebox sits in the viewframe
	 //hence z translate the plane wrt to the view

	 t5.SetTranslation(0, 0,(vnb-1./2.)*fDeltaz_view+(pnb-1./2.)*fDeltaz_plane12);	
	 TGeoCombiTrans d5(t5, r5); 
	 TGeoHMatrix *j5 = new TGeoHMatrix(d5);
	 vetovac->AddNode(planebox, statnb*10000000+vnb*1000000+pnb*100000,j5); 
	   	
         for (Int_t lnb=0; lnb<2; lnb++) {
           TString nmlayer = nmplane+"_layer_"; nmlayer += lnb;
	   //width of the layer: (plane width-2eps)/2
	   TGeoBBox *layer = new TGeoBBox("layer box", fStraw_length+eps/4, yDim+eps/4, layerwidth/2.+eps/4);
           TGeoVolume *layerbox = new TGeoVolume(nmlayer, layer, med);      
	   //z translate the layerbox wrt the plane box (which is already rotated)	          	
	   planebox->AddNode(layerbox, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  	
	   //layer loop
	   TGeoRotation r6v;	
	   TGeoTranslation t6v;
           Int_t nr = statnb*10000000+vnb*1000000+pnb*100000+lnb*10000;
             for (Int_t snb=1; snb<fStraws_per_layer; snb++) {
               //straw loop
	       t6v.SetTranslation(0,yDim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12,0); 	
	       r6v.SetAngles(90,90,0);
	       TGeoCombiTrans c6v(t6v, r6v);
               TGeoHMatrix *h6v = new TGeoHMatrix(c6v);

	       layerbox->AddNode(straw,nr+1000+snb,h6v);
	       layerbox->AddNode(gas,  nr+2000+snb,h6v);
               layerbox->AddNode(wire, nr+3000+snb,h6v);
	     //end of straw loop
           }
	   //end of layer loop
        }
        //end of plane loop	 	
      }
      //end of view loop
     }
     // end of veto station loop

    //Tracking stations
    //statnb=station number; vnb=view number; pnb=plane number; lnb=layer number; snb=straw number
    
    TGeoBBox *vacbox = new TGeoBBox("vacbox",  fVacBox_x, fVacBox_y, 2.*fDeltaz_view );

    for (statnb=1;statnb<5;statnb++) {
       // tracking station loop
       TString nmstation = "Tr"; nmstation += statnb;	

       switch (statnb) {
	   case 1:
	      TStationz=fT1z;
	      break;
	   case 2:
	      TStationz=fT2z;
	      break;
	   case 3:
	      TStationz=fT3z;
	      break;
	   case 4:
	      TStationz=fT4z;
	      break;
	   default:
	      break;
       }
       
       TGeoVolume *vac = new TGeoVolume(nmstation, vacbox, med);
       top->AddNode(vac, statnb, new TGeoTranslation(0,0,TStationz));
       
       for (Int_t vnb=0; vnb<4; vnb++) {
        //view loop
        TString nmview;
        Double_t angle;
        TGeoRotation r5;	
	TGeoTranslation t5; 	
		
        switch (vnb) {
	   case 0:
	      angle=0.;
	      nmview = nmstation+"_x1";
	      break;
	   case 1:
	      angle=fView_angle;
	      nmview = nmstation+"_u";
	      break;
	   case 2:
	      angle=-fView_angle;
	      nmview = nmstation+"_v";
	      break;
	   case 3:
	      angle=0.;
	      nmview = nmstation+"_x2";
	      break;
	   default:
	      angle=0.;
	      nmview = nmstation+"_x1";
         }	

         TGeoVolume *viewframe = new TGeoVolume(nmview, detcomp1, Al);
	 //z-translate the viewframe from station z pos
	 t5.SetTranslation(0, 0,(vnb-3./2.)*(fDeltaz_view));
	 //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)	
         r5.SetAngles(angle,0,0);
         TGeoCombiTrans c5(t5, r5);
         TGeoHMatrix *h5 = new TGeoHMatrix(c5);	
	 vac->AddNode(viewframe, statnb*10000000+vnb*1000000,h5);
         viewframe->SetLineColor(kRed);
 	 	
         for (Int_t pnb=0; pnb<2; pnb++) {
	   //plane loop
           TString nmplane = nmview+"_plane_"; nmplane += pnb;
	   //width of the planes: z distance between layers + outer straw diameter
	   TGeoBBox *plane = new TGeoBBox("plane box", fStraw_length+eps/2, yDim+eps/2, planewidth/2.+eps/2);
           TGeoVolume *planebox = new TGeoVolume(nmplane, plane, med);
	   //the planebox sits in the viewframe
	   //hence z translate the plane wrt to the view
	   TGeoTranslation t3;
	   t3.SetTranslation(0, 0,(vnb-3./2.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12);	
	   TGeoCombiTrans d3(t3, r5); 
	   TGeoHMatrix *j3 = new TGeoHMatrix(d3);	  
	   vac->AddNode(planebox, statnb*10000000+vnb*1000000+pnb*100000,j3); 
	
           for (Int_t lnb=0; lnb<2; lnb++) {
             TString nmlayer = nmplane+"_layer_"; nmlayer += lnb;
	     //width of the layer: (plane width-2*eps)/2
	     TGeoBBox *layer = new TGeoBBox("layer box", fStraw_length+eps/4, yDim+eps/4, layerwidth/2.+eps/4);
             TGeoVolume *layerbox = new TGeoVolume(nmlayer, layer, med);
	     //z translate the layerbox wrt the plane box (which is already rotated)
	     planebox->AddNode(layerbox, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  	
             //layer loop
	     TGeoRotation r6s;	
	     TGeoTranslation t6s;
             for (Int_t snb=1; snb<fStraws_per_layer; snb++) {
               //straw loop
	       t6s.SetTranslation(0,yDim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12,0); 	
               r6s.SetAngles(90,90,0);
	       TGeoCombiTrans c6s(t6s, r6s);
               TGeoHMatrix *h6s = new TGeoHMatrix(c6s);

	       layerbox->AddNode(straw,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb,h6s);
	       layerbox->AddNode(gas,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+2000+snb,h6s);
               layerbox->AddNode(wire,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+3000+snb,h6s);

	     //end of straw loop
             }
	  //end of layer loop
          }
	 //end of plane loop		
         }
	//end of view loop
        }
     //end of station
     }
}
// -----   Public method StrawDecode    -------------------------------------------
// -----   returns station layer ... numbers -----------------------------------
void strawtubes::StrawDecode(Int_t detID,int &statnb,int &vnb,int &pnb,int &lnb, int &snb)
{
  statnb = detID/10000000;
  vnb =  (detID - statnb*10000000)/1000000;
  pnb =  (detID - statnb*10000000 - vnb*1000000)/100000;
  lnb =  (detID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
  snb =   detID - statnb*10000000 - vnb*1000000 - pnb*100000 - lnb*10000 - 2000;
}
// -----   Public method StrawEndPoints    -------------------------------------------
// -----   returns top(left) and bottom(right) coordinate of straw -----------------------------------
void strawtubes::StrawEndPoints(Int_t detID, TVector3 &bot, TVector3 &top)
{
  Double_t eps=0.1;
  Double_t sinangle,cosangle;
  Int_t statnb,vnb,pnb,lnb,snb;
  StrawDecode(detID,statnb,vnb,pnb,lnb,snb);
  switch (vnb) {
     case 0:
       sinangle=0.; 
       cosangle=1.; 
       break;
     case 1:
       sinangle=fsinphi; 
       cosangle=fcosphi; 
       break;     
     case 2:
       sinangle=-fsinphi; 
       cosangle=fcosphi; 
       break; 
     case 3:
       sinangle=0.; 
       cosangle=1.; 
       break; 
     default:
       sinangle=0.; 
       cosangle=1.; 
   }   

  //cout << "DetID" << detID << " statnb "<<statnb<<" vnb " << vnb << " pnb " << pnb <<" lnb "<< lnb << " snb " << snb << endl;
  // from ConstructGeometry above
  Double_t yDim =  (fStraws_per_layer+1) * fStraw_pitch /2. ; 
  Double_t ypos = yDim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12; 	
  Double_t xtop = -fStraw_length*cosangle - ypos*sinangle;
  Double_t ytop = -fStraw_length*sinangle + ypos*cosangle;
  Double_t xbot =  fStraw_length*cosangle - ypos*sinangle;
  Double_t ybot =  fStraw_length*sinangle + ypos*cosangle;
  Double_t TStationz;
  switch (statnb) {
     case 1:
       TStationz = fT1z; 
       break;
     case 2:
       TStationz = fT2z; 
       break;
     case 3:
       TStationz = fT3z; 
       break;
     case 4:
       TStationz = fT4z; 
       break;
     default:
       TStationz = fT0z;  
   }                           
  Double_t zpos = TStationz+(vnb-3./2.)*fDeltaz_view+(pnb-1./2.)*fDeltaz_plane12+(lnb-1./2.)*fDeltaz_layer12;
  top = TVector3(xtop,ytop,zpos);
  bot = TVector3(xbot,ybot,zpos);
  //cout << "dets="<< xtop << " "<< xbot << " "<<  ytop << " "<< ybot<< " "<< ypos<< " "<< fStraw_length<< " "<<detID<<endl;
  //cout << "top/bot="<< snb << " "<< vnb << " "<<  pnb << " "<< lnb << " "<< ypos<< " "<< fOffset_layer12<< " "<<fOffset_plane12<<endl;
}
strawtubesPoint* strawtubes::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode, Double_t dist2Wire)
{
  TClonesArray& clref = *fstrawtubesPointCollection;
  Int_t size = clref.GetEntriesFast();
  //cout << "strawtubes hit called pos.z="<< pos.z()<< " detID= "<<detID<<endl;
  return new(clref[size]) strawtubesPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode, dist2Wire);
}

ClassImp(strawtubes)
