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


#include <iostream>
using std::cout;
using std::endl;

strawtubes::strawtubes()
  : FairDetector("strawtubes", kTRUE, kVETO),
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
  : FairDetector(name, active, kVETO),
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
    //fVacbox_x(300.),                 //!  x of station vacuum box
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
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    fVolumeID = vol->getMCid();
    if (fELoss == 0. ) { return kFALSE; }
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss);
    // Increment number of strawtubes det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    std::cout << "+add straw point"<<std::endl;
    stack->AddPoint(kVETO);
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
     //std::cout << "++++++++++++++++++++++++++++++++++++++++++++++"<<std::endl;
     //std::cout << "setting z positions " << fT0z << " " << fT1z << fT2z << " " << fT3z << " " << fT4z << std::endl;
     //std::cout << "++++++++++++++++++++++++++++++++++++++++++++++"<<std::endl;
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

    //gGeoManager->SetVisLevel(6); //depth level painted - default 3
    //gGeoManager->SetVisOption(0); //0 show all nodes down to vislevel
    //gGeoManager->SetTopVisible();
    std::cout << "start straw geo"<<std::endl;
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

    //epsilon to avoid overlapping volumes
    Double_t eps=0.0001;
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

    //arguments of box are half-lengths
    TGeoBBox *detbox1 = new TGeoBBox("detbox1", fStraw_length+5., fStraw_length+5., fDeltaz_view/2.);
    TGeoBBox *detbox2 = new TGeoBBox("detbox2", fStraw_length+eps, fStraw_length+eps, fDeltaz_view/2.);

    //the station sits inside a vacuum box
    TGeoBBox *vetovacbox = new TGeoBBox("Vetovacbox", fVacBox_x, fVacBox_y, fDeltaz_view+eps );


    TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");

    TGeoVolume *vetovac = new TGeoVolume("Veto", vetovacbox, med);
    //vetovac->SetVisibility(kFALSE);
    //vetovac->VisibleDaughters(kTRUE);
    top->AddNode(vetovac, 1, new TGeoTranslation(0, 0, fT0z));


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
      t5.SetTranslation(0, 0,(vnb-1./2.)*(fDeltaz_view));
      //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)	
      r5.SetAngles(angle,0,0);
      TGeoCombiTrans c5(t5, r5);
      TGeoHMatrix *h5 = new TGeoHMatrix(c5);	
      vetovac->AddNode(viewframe, 4*10000000+vnb*1000000,h5);
      //viewframe->SetVisibility(kTRUE);
      //viewframe->VisibleDaughters(kTRUE);
      viewframe->SetLineColor(kRed);

      TGeoTranslation t5p;
	 	
      for (Int_t pnb=0; pnb<2; pnb++) {
	 //plane loop
         TString nmplane = nmview+"_plane_"; nmplane += pnb;
	 //width of the planes: z distance between layers + outer straw diameter
	 TGeoBBox *plane = new TGeoBBox("plane box", fStraw_length-eps, fStraw_length-eps, planewidth/2.);
         TGeoVolume *planebox = new TGeoVolume(nmplane, plane, med);
	 //the planebox sits in the viewframe
	 //hence z translate the plane wrt to the view
	 viewframe->AddNode(planebox, 4*10000000+vnb*1000000+pnb*100000,new TGeoTranslation(0, 0,(pnb-1./2.)*fDeltaz_plane12));
	 planebox->SetVisibility(kFALSE);
         //planebox->VisibleDaughters(kTRUE);

    /*     TGeoRotation r5l;	
	 TGeoTranslation t5l; 	
         for (Int_t lnb=0; lnb<2; lnb++) {
           TString nmlayer = nmplane+"_layer_"; nmlayer += lnb;
	   //width of the layer: (plane width-2eps)/2
	   TGeoBBox *layer = new TGeoBBox("layer box", fStraw_length-2*eps, fStraw_length-2*eps, layerwidth/2.);
           TGeoVolume *layerbox = new TGeoVolume(nmlayer, layer, med);
	   //z translate the layerbox wrt the plane box (which is already rotated)	          	
	   planebox->AddNode(layerbox, 4*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  	
	   //layerbox->SetVisibility(kFALSE);
           //layerbox->VisibleDaughters(kTRUE);	
	   //std::cout <<nmlayer<<"veto zpos "<<TStationz-(1./2.-vnb)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12+(lnb-1./2.)*fDeltaz_layer12<<std::endl;
	   //layer loop
	   TGeoRotation r5s;	
	   TGeoTranslation t5s;
           for (Int_t snb=0; snb<fStraws_per_layer; snb++) {
             //straw loop
	     t5s.SetTranslation(fStraw_length-fStraw_pitch*snb-8*eps+fOffset_plane12*pnb+lnb*fOffset_layer12, 0,0); 	
	     //straws are tubes defined along the z-axis, so need to rotate them first by 90 degrees around the x-axis to get them vertical
	     //then x translate the straws according to their plane, layer and number
	     r5s.SetAngles(0,90,0);
	     TGeoCombiTrans c5s(t5s, r5s);
             TGeoHMatrix *h5s = new TGeoHMatrix(c5s);
	
             // Volume: straw
             rmin = fInner_Straw_diameter/2.;
             rmax = fOuter_Straw_diameter/2.;
             TString nmstraw = nmlayer+"_straw_"; nmstraw += snb;
	     //third argument is halflength of tube
             TGeoTube *straw_tube = new TGeoTube(nmstraw,rmin,rmax,fStraw_length-4.*eps);
	     TGeoVolume *straw = new TGeoVolume(nmstraw,straw_tube, mylar);
             straw->SetLineColor(4);
	     //straw->SetVisibility(kTRUE);

             // Volume: gas
             rmin = fWire_thickness+eps;
             rmax = fInner_Straw_diameter/2.-eps;
             TString nmgas = nmlayer+"_gas_"; nmgas += snb;
             TGeoTube *gas_tube = new TGeoTube(nmgas,rmin,rmax,fStraw_length-6.*eps);
	     TGeoVolume *gas = new TGeoVolume(nmgas,gas_tube, sttmix9010_2bar);
             gas->SetLineColor(5);
	     //gas->SetVisibility(kTRUE);

             // Volume: wire
             rmin=0.;
             rmax = fWire_thickness;
             TString nmwire = nmlayer+"_wire_"; nmwire += snb;
             TGeoTube *wire_tube = new TGeoTube("wire",rmin,rmax,fStraw_length-8.*eps);
	     TGeoVolume *wire = new TGeoVolume(nmwire,wire_tube, tungsten);
             wire->SetLineColor(6);
	     //wire->SetVisibility(kTRUE);

	     layerbox->AddNode(straw,4*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb,h5s);
             AddSensitiveVolume(straw);
	     layerbox->AddNode(gas,4*10000000+vnb*1000000+pnb*100000+lnb*10000+2000+snb,h5s);
             layerbox->AddNode(wire,4*10000000+vnb*1000000+pnb*100000+lnb*10000+3000+snb,h5s);
	     //only the straws are sensitive

	     //end of straw loop
           }
	   //end of layer loop
        }*/
        //end of plane loop	 	
      }
      //end of view loop
     }
     // end of veto station loop

    //Tracking stations
    //statnb=station number; vnb=view number; pnb=plane number; lnb=layer number; snb=straw number
    TGeoBBox *vacbox = new TGeoBBox("vacbox",  fVacBox_x, fVacBox_y, 2.*fDeltaz_view+eps );

    for (Int_t statnb=0;statnb<4;statnb++) {
       // tracking station loop
       TString nmstation = "Tr"; nmstation += statnb;	

       switch (statnb) {
	   case 0:
	      TStationz=fT1z;
	      break;
	   case 1:
	      TStationz=fT2z;
	      break;
	   case 2:
	      TStationz=fT3z;
	      break;
	   case 3:
	      TStationz=fT4z;
	      break;
	   default:
	      break;
       }

       TGeoVolume *vac = new TGeoVolume(nmstation, vacbox, med);
       //vac->SetVisibility(kFALSE);
       //vac->VisibleDaughters(kTRUE);
       top->AddNode(vac, 5, new TGeoTranslation(0, 0, TStationz));	

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
	 //viewframe->SetVisibility(kTRUE);
	 //viewframe->VisibleDaughters(kTRUE);
         viewframe->SetLineColor(kRed);

               // Volume: straw
               rmin = fInner_Straw_diameter/2.;
               rmax = fOuter_Straw_diameter/2.;
	       //third argument is halflength of tube
               TGeoTube *straw_tube = new TGeoTube("_straw_",rmin,rmax,fStraw_length-4.*eps);
 	       TGeoVolume *straw = new TGeoVolume("_straw_",straw_tube, mylar);
               straw->SetLineColor(4);
	       //straw->SetVisibility(kTRUE);
               AddSensitiveVolume(straw);
 	
               // Volume: gas
               rmin = fWire_thickness+eps;
               rmax = fInner_Straw_diameter/2.-eps;
               TGeoTube *gas_tube = new TGeoTube("_gas_",rmin,rmax,fStraw_length-6.*eps);
 	       TGeoVolume *gas = new TGeoVolume("_gas_",gas_tube, sttmix9010_2bar);
               gas->SetLineColor(5);
	       //gas->SetVisibility(kTRUE);

               // Volume: wire
               rmin=0.;
               rmax = fWire_thickness;
               TGeoTube *wire_tube = new TGeoTube("wire",rmin,rmax,fStraw_length-8.*eps);
 	       TGeoVolume *wire = new TGeoVolume("_wire_",wire_tube, tungsten);
               wire->SetLineColor(6);
	       //wire->SetVisibility(kTRUE);
	 	
        for (Int_t pnb=0; pnb<2; pnb++) {
	   //plane loop
           TString nmplane = nmview+"_plane_"; nmplane += pnb;
	   //width of the planes: z distance between layers + outer straw diameter
	   TGeoBBox *plane = new TGeoBBox("plane box", fStraw_length-eps, fStraw_length-eps, planewidth/2.);
           TGeoVolume *planebox = new TGeoVolume(nmplane, plane, med);
	   //the planebox sits in the viewframe
	   //hence z translate the plane wrt to the view
	   viewframe->AddNode(planebox, statnb*10000000+vnb*1000000+pnb*100000,new TGeoTranslation(0, 0,(pnb-1./2.)*fDeltaz_plane12));
	   //planebox->SetVisibility(kFALSE);
           //planebox->VisibleDaughters(kTRUE);
           TGeoRotation r5l;	
	   TGeoTranslation t5l; 	
           for (Int_t lnb=0; lnb<2; lnb++) {
             TString nmlayer = nmplane+"_layer_"; nmlayer += lnb;
	     //width of the layer: (plane width-2eps)/2
	     TGeoBBox *layer = new TGeoBBox("layer box", fStraw_length-2*eps, fStraw_length-2*eps, layerwidth/2.);
             TGeoVolume *layerbox = new TGeoVolume(nmlayer, layer, med);
	     //z translate the layerbox wrt the plane box (which is already rotated)
	     planebox->AddNode(layerbox, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  	
	     //layerbox->SetVisibility(kTRUE);
	     //layerbox->VisibleDaughters(kTRUE);
	     //std::cout <<nmlayer<<" zpos "<<TStationz-(1./2.-vnb)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12+(lnb-1./2.)*fDeltaz_layer12<<std::endl;		
	
             //layer loop
	     TGeoRotation r6s;	
	     TGeoTranslation t6s;
             for (Int_t snb=0; snb<fStraws_per_layer; snb++) {
               //straw loop
	       t6s.SetTranslation(fStraw_length-fStraw_pitch*snb-8*eps+fOffset_plane12*pnb+lnb*fOffset_layer12, 0,0); 	
	       //straws are tubes defined along the z-axis, so need to rotate them first by 90 degrees around the x-axis to get them vertical
	       //then x translate the straws according to their plane, layer and number
               r6s.SetAngles(0,90,0);
	       TGeoCombiTrans c6s(t6s, r6s);
               TGeoHMatrix *h6s = new TGeoHMatrix(c6s);
	

	       layerbox->AddNode(straw,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb,h6s);
	       layerbox->AddNode(gas,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+2000+snb,h6s);
               layerbox->AddNode(wire,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+3000+snb,h6s);
	       //only the straws are sensitive

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
    std::cout << "end straw geo"<<std::endl;
}

strawtubesPoint* strawtubes::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss)
{
  TClonesArray& clref = *fstrawtubesPointCollection;
  Int_t size = clref.GetEntriesFast();
  cout << "strawtubes hit called pos.z="<< pos.z()<< " detID= "<<detID<<endl;
  return new(clref[size]) strawtubesPoint(trackID, detID, pos, mom,
         time, length, eLoss);
}

ClassImp(strawtubes)
