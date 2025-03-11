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
#include <sstream>
using std::cout;
using std::endl;

strawtubes::strawtubes()
    : FairDetector("Strawtubes", kTRUE, kStraw)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fMedium("air")
    , fstrawtubesPointCollection(new TClonesArray("strawtubesPoint"))
{}

strawtubes::strawtubes(std::string medium)
    : FairDetector("Strawtubes", kTRUE, kStraw)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fMedium(medium)
    , fstrawtubesPointCollection(new TClonesArray("strawtubesPoint"))
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
    gMC->CurrentVolID(straw_uniqueId);
    if (fVolumeID == straw_uniqueId) {
        //std::cout << pdgCode<< " same volume again ? "<< straw_uniqueId << " exit:" << gMC->IsTrackExiting() << " stop:" << gMC->IsTrackStop() << " disappeared:" << gMC->IsTrackDisappeared()<< std::endl;
         return kTRUE; }
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
    TVector3 v  = TVector3(fPos.X()-Pos.X(),fPos.Y()-Pos.Y(),fPos.Z()-Pos.Z());
    TVector3 uCrossv = u.Cross(v);
    Double_t dist2Wire  = fabs(pq.Dot(uCrossv))/(uCrossv.Mag()+1E-8);
    Double_t deltaTrackLength = gMC->TrackLength() - fLength;
    AddHit(fTrackID, straw_uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, deltaTrackLength,
           fELoss,pdgCode,dist2Wire);
    if (dist2Wire>fInner_Straw_diameter/2){
     std::cout << "addhit " << dist2Wire<< " straw id " << straw_uniqueId << " pdgcode " << pdgCode<< " dot prod " << pq.Dot(uCrossv)<< std::endl;
     std::cout << " exit:" << gMC->IsTrackExiting() << " stop:" << gMC->IsTrackStop() << " disappeared:" << gMC->IsTrackDisappeared()<< std::endl;
     std::cout << " entry:" << fPos.X()<< " " << fPos.Y()<< " " << fPos.Z() << std::endl;
     std::cout << " exit:" << Pos.X()<< " " << Pos.Y()<< " " << Pos.Z() << std::endl;
     std::cout << " mean:" << xmean<< " " << ymean << " " << zmean << std::endl;
     std::cout << " bot:" << bot.x()<< " " << bot.y() << " " << bot.z() << std::endl;
     std::cout << " top:" << top.x()<< " " << top.y() << " " << top.z() << std::endl;
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
void strawtubes::SetZpositions(Double_t z0, Double_t z1, Double_t z2, Double_t z3, Double_t z4)
{
     fT0z = z0;                                                 //!  z-position of veto station
     fT1z = z1;                                                 //!  z-position of tracking station 1
     fT2z = z2;                                                 //!  z-position of tracking station 2
     fT3z = z3;                                                 //!  z-position of tracking station 3
     fT4z = z4;                                                 //!  z-position of tracking station 4
}

void strawtubes::SetStrawLength(Double_t strawlength)
{
     fStraw_length = strawlength;                               //!  Length (y) of a straw
}

void strawtubes::SetInnerStrawDiameter(Double_t innerstrawdiameter)
{
     fInner_Straw_diameter = innerstrawdiameter;                //!  Inner Straw diameter
}

void strawtubes::SetOuterStrawDiameter(Double_t outerstrawdiameter)
{
     fOuter_Straw_diameter = outerstrawdiameter;                //!  Outer Straw diameter
}


void strawtubes::SetStrawPitch(Double_t strawpitch,Double_t layer_offset, Double_t plane_offset)
{
     fStraw_pitch = strawpitch;                                 //!  Distance (x) between straws in one layer
     fOffset_layer12 = layer_offset;
     fOffset_plane12 = plane_offset;
}

void strawtubes::SetDeltazLayer(Double_t deltazlayer)
{
     fDeltaz_layer12 = deltazlayer;                              //! Distance (z) between layer 1&2
}

void strawtubes::SetDeltazPlane(Double_t deltazplane)
{
     fDeltaz_plane12 = deltazplane;                              //! Distance (z) between plane 1&2
}

void strawtubes::SetStrawsPerLayer(Int_t strawsperlayer)
{
     fStraws_per_layer = strawsperlayer;                         //! number of straws in one layer
}

void strawtubes::SetStereoAngle(Double_t stereoangle)
{
     fView_angle = stereoangle;                                  //! Stereo angle of planes in a view
     fcosphi=cos(TMath::Pi()*fView_angle/180.);
     fsinphi=sin(TMath::Pi()*fView_angle/180.);
}

void strawtubes::SetWireThickness(Double_t wirethickness)
{
     fWire_thickness = wirethickness;                            //! Thickness of the wire
}

void strawtubes::SetDeltazView(Double_t deltazview)
{
     fDeltaz_view = deltazview;                                  //! Distance (z) between views
}

void strawtubes::SetDeltazFrame(Double_t deltazframe)
{
        fDeltaz_frame = deltazframe;                             //! Thickness (z) of the meterial frame
}

void strawtubes::SetFrameLateralWidth(Double_t framelateralwidth)
{
        fFrame_lateral_width = framelateralwidth;                //! Width (x and y) of the material frame
}

void strawtubes::SetFrameMaterial(TString framematerial)
{
        fFrame_material = framematerial;                         //! Material of the view frame
}


void strawtubes::SetStrawLength12(Double_t strawlength12)
{
     fStraw_length_12 = strawlength12;                             //! strawlength of stations 1,2
}

void strawtubes::SetStrawLengthVeto(Double_t strawlengthveto)
{
     fStraw_length_veto = strawlengthveto;                         //! strawlength of veto station
}


void strawtubes::SetVacBox_x(Double_t vacbox_x)
{
     fVacBox_x = vacbox_x;                               //! x size of station vacuum box
}

void strawtubes::SetVacBox_y(Double_t vacbox_y)
{
     fVacBox_y = vacbox_y;                               //! y size of station vacuum box
}

void strawtubes::SetVetoYDim(Double_t vetoydim)
{
     fvetoydim = vetoydim;                               //! y size of veto
     fStraws_per_layer_veto= (Int_t) (2.*fvetoydim/fStraw_pitch);
     //std::cout<<"fStraws_per_layer_veto "<<fStraws_per_layer_veto<<" fvetoydim "<< fvetoydim<<std::endl;
}
void strawtubes::SetTr12YDim(Double_t tr12ydim)
{
     ftr12ydim = tr12ydim;
     fStraws_per_layer_tr12= (Int_t) (2.*ftr12ydim/fStraw_pitch);      //! y size of stations 12
     //std::cout<<"fStraws_per_layer_tr12 "<<fStraws_per_layer_tr12<< " ftr12ydim "<< ftr12ydim <<std::endl;
}
void strawtubes::SetTr34YDim(Double_t tr34ydim)
{
     ftr34ydim = tr34ydim;                               //! y size of stations 34
     fStraws_per_layer_tr34= (Int_t) (2.*ftr34ydim/fStraw_pitch);
     //std::cout<<"fStraws_per_layer_tr34 "<<fStraws_per_layer_tr34<<" ftr34ydim "<< ftr34ydim << std::endl;
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
    InitMedium(fFrame_material);
    TGeoMedium *FrameMatPtr       = gGeoManager->GetMedium(fFrame_material);
    InitMedium(fMedium.c_str());
    TGeoMedium* med = gGeoManager->GetMedium(fMedium.c_str());

    gGeoManager->SetVisLevel(4);
    gGeoManager->SetTopVisible();

    //epsilon to avoid overlapping volumes
    //Double_t eps=0.1;
    Double_t eps=0.0001;
    Double_t epsS=0.0001;
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
    TGeoBBox *detbox1 = new TGeoBBox("detbox1", fStraw_length+fFrame_lateral_width,  ftr34ydim+fFrame_lateral_width, fDeltaz_frame/2.);
    TGeoBBox *detbox2 = new TGeoBBox("detbox2", fStraw_length+eps, ftr34ydim+eps, fDeltaz_frame/2.+eps);

    TGeoBBox *detbox1_12 = new TGeoBBox("detbox1_12", fStraw_length_12+fFrame_lateral_width,  ftr12ydim+fFrame_lateral_width, fDeltaz_frame/2.);
    TGeoBBox *detbox2_12 = new TGeoBBox("detbox2_12", fStraw_length_12+eps, ftr12ydim+eps, fDeltaz_frame/2.+eps);
    TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");
    TGeoCompositeShape *detcomp1_12 = new TGeoCompositeShape("detcomp1_12", "detbox1_12-detbox2_12");
    TGeoBBox *vetovacbox;
    TGeoCompositeShape *detcomp1_veto;
    if (fStraw_length_veto>1){
     TGeoBBox *detbox1_veto = new TGeoBBox("detbox1_veto", fStraw_length_veto+1.,  fvetoydim+1., fDeltaz_view/2.);
     TGeoBBox *detbox2_veto = new TGeoBBox("detbox2_veto", fStraw_length_veto+eps, fvetoydim+eps, fDeltaz_view/2.+eps);

    //the station sits inside a vacuum box
    //TGeoBBox *vetovacbox = new TGeoBBox("Vetovacbox", fVacBox_x, fVacBox_y, fDeltaz_view );
     vetovacbox = new TGeoBBox("Vetovacbox", fStraw_length_veto+75., fvetoydim+75., fDeltaz_view );
     detcomp1_veto = new TGeoCompositeShape("detcomp1_veto", "detbox1_veto-detbox2_veto");
    }
    // Volume: straw
    rmin = fInner_Straw_diameter/2.;
    rmax = fOuter_Straw_diameter/2.;
    //third argument is halflength of tube
    TGeoTube *straw_tube = new TGeoTube("straw",rmin,rmax,fStraw_length-4.*eps);
    TGeoVolume *straw = new TGeoVolume("straw",straw_tube, mylar);
    straw->SetLineColor(4);
    straw->SetVisibility(kTRUE);
    TGeoTube *straw_tube_12 = new TGeoTube("straw_12",rmin,rmax,fStraw_length_12-4.*eps);
    TGeoVolume *straw_12 = new TGeoVolume("straw_12",straw_tube_12, mylar);
    straw_12->SetLineColor(4);
    straw_12->SetVisibility(kTRUE);
    TGeoVolume *straw_veto;
    if (fStraw_length_veto>1){
     TGeoTube *straw_tube_veto = new TGeoTube("straw_veto",rmin,rmax,fStraw_length_veto-4.*eps);
     straw_veto = new TGeoVolume("straw_veto",straw_tube_veto, mylar);
     straw_veto->SetLineColor(4);
     straw_veto->SetVisibility(kTRUE);
    }
    // Volume: gas
    rmin = fWire_thickness/2.+epsS;
    rmax = fInner_Straw_diameter/2.-epsS;
    TGeoTube *gas_tube = new TGeoTube("gas",rmin,rmax,fStraw_length-6.*eps);
    TGeoVolume *gas = new TGeoVolume("gas",gas_tube, sttmix9010_2bar);
    gas->SetLineColor(5);    //only the gas is sensitive
    AddSensitiveVolume(gas);
    TGeoTube *gas_tube_12 = new TGeoTube("gas_12",rmin,rmax,fStraw_length_12-6.*eps);
    TGeoVolume *gas_12 = new TGeoVolume("gas_12",gas_tube_12, sttmix9010_2bar);
    gas_12->SetLineColor(5);    //only the gas is sensitive
    AddSensitiveVolume(gas_12);
    TGeoVolume *gas_veto;
    TGeoBBox *layer_veto;
    if (fStraw_length_veto>1){
     TGeoTube *gas_tube_veto = new TGeoTube("gas_veto",rmin,rmax,fStraw_length_veto-6.*eps);
     gas_veto = new TGeoVolume("gas_veto",gas_tube_veto, sttmix9010_2bar);
     gas_veto->SetLineColor(5);    //only the gas is sensitive
     AddSensitiveVolume(gas_veto);
    }

    // Volume: wire
    rmin=0.;
    rmax = fWire_thickness/2.;
    TGeoTube *wire_tube = new TGeoTube("wire",rmin,rmax,fStraw_length-8.*eps);
    TGeoVolume *wire = new TGeoVolume("wire",wire_tube, tungsten);
    wire->SetLineColor(6);
    TGeoTube *wire_tube_12 = new TGeoTube("wire_12",rmin,rmax,fStraw_length_12-8.*eps);
    TGeoVolume *wire_12 = new TGeoVolume("wire_12",wire_tube_12, tungsten);
    wire_12->SetLineColor(6);
    Int_t statnb;
    if (fStraw_length_veto>1){
     TGeoTube *wire_tube_veto = new TGeoTube("wire_veto",rmin,rmax,fStraw_length_veto-8.*eps);
     TGeoVolume *wire_veto = new TGeoVolume("wire_veto",wire_tube_veto, tungsten);
     wire_veto->SetLineColor(6);
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
      Double_t angle;
      TGeoRotation r5;
      TGeoTranslation t5;
      nmveto = "Veto";
      switch (vnb) {
	   case 0:
	      angle=0.;
	      nmveto = nmveto+"_x";
	      break;
	   case 1:
	      angle=fView_angle;
	      nmveto = nmveto+"_u";
	      break;
	   default:
	      angle=0.;
	      nmveto = nmveto+"_x";
      }

      TGeoVolume *viewframe_veto = new TGeoVolume(nmveto, detcomp1_veto, Al);
      //z-translate the viewframe_veto from station z pos
      t5.SetTranslation(0, 0,(vnb-1./2.)*fDeltaz_view);
      //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)
      r5.SetAngles(angle,0,0);
      TGeoCombiTrans c5(t5, r5);
      TGeoHMatrix *h5 = new TGeoHMatrix(c5);
      vetovac->AddNode(viewframe_veto, statnb*10000000+vnb*1000000,h5);
      viewframe_veto->SetLineColor(kRed);

      TGeoTranslation t5p;

      for (Int_t pnb=0; pnb<1; pnb++) {
	 //plane loop
         TString nmplane_veto = nmveto+"_plane_"; nmplane_veto += pnb;
	 //width of the planes: z distance between layers + outer straw diameter
	 TGeoBBox *plane_veto = new TGeoBBox("plane box", fStraw_length_veto+eps/2., fvetoydim+eps/2., planewidth/2.+3.*eps/2.);
         TGeoVolume *planebox_veto = new TGeoVolume(nmplane_veto, plane_veto, med);
	 //the planebox sits in the viewframe
	 //hence z translate the plane wrt to the view

	 t5.SetTranslation(0, 0,(vnb-1./2.)*fDeltaz_view+(pnb-1./2.)*fDeltaz_plane12);
	 TGeoCombiTrans d5(t5, r5);
	 TGeoHMatrix *j5 = new TGeoHMatrix(d5);
	 vetovac->AddNode(planebox_veto, statnb*10000000+vnb*1000000+pnb*100000,j5);

         for (Int_t lnb=0; lnb<2; lnb++) {
           TString nmlayer_veto = nmplane_veto+"_layer_"; nmlayer_veto += lnb;
	   //width of the layer: (plane width-2eps)/2
	   layer_veto = new TGeoBBox("layer box_veto", fStraw_length_veto+eps/4., fvetoydim+eps/4., layerwidth/2.+eps/4.);
           TGeoVolume *layerbox_veto = new TGeoVolume(nmlayer_veto, layer_veto, med);
	   //z translate the layerbox wrt the plane box (which is already rotated)
	   planebox_veto->AddNode(layerbox_veto, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12));
	   //layer loop
	   TGeoRotation r6v;
	   TGeoTranslation t6v;
           Int_t nr = statnb*10000000+vnb*1000000+pnb*100000+lnb*10000;
             for (Int_t snb=1; snb<fStraws_per_layer_veto; snb++) {
               //straw loop
	       t6v.SetTranslation(0,fvetoydim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12,0);
	       r6v.SetAngles(90,90,0);
	       TGeoCombiTrans c6v(t6v, r6v);
               TGeoHMatrix *h6v = new TGeoHMatrix(c6v);

	       layerbox_veto->AddNode(straw_veto,nr+1000+snb,h6v);
	       layerbox_veto->AddNode(gas_veto,  nr+2000+snb,h6v);
               layerbox_veto->AddNode(wire_veto, nr+3000+snb,h6v);
	     //end of straw loop
           }
	   //end of layer loop
        }
        //end of plane loop
      }
      //end of view loop
     } }
     // end of veto station loop
    //Tracking stations
    //statnb=station number; vnb=view number; pnb=plane number; lnb=layer number; snb=straw number

    //New scalable endpoints of vacuum boxes which cover rotated view frames

    Double_t x_prime = (fVacBox_x+0.6*fFrame_lateral_width+2*eps)*TMath::Cos(fView_angle*TMath::Pi()/180.0) + (ftr34ydim+fFrame_lateral_width+2*eps)*TMath::Sin(fView_angle*TMath::Pi()/180.0);
    Double_t y_prime = (fVacBox_x+0.6*fFrame_lateral_width+2*eps)*TMath::Sin(fView_angle*TMath::Pi()/180.0) + (ftr34ydim+fFrame_lateral_width+2*eps)*TMath::Cos(fView_angle*TMath::Pi()/180.0);
        Double_t x_prime_12 = (fStraw_length_12+fFrame_lateral_width+2*eps)*TMath::Cos(fView_angle*TMath::Pi()/180.0) + (ftr12ydim+fFrame_lateral_width+2*eps)*TMath::Sin(fView_angle*TMath::Pi()/180.0);
    Double_t y_prime_12 = (fStraw_length_12+fFrame_lateral_width+2*eps)*TMath::Sin(fView_angle*TMath::Pi()/180.0) + (ftr12ydim+fFrame_lateral_width+2*eps)*TMath::Cos(fView_angle*TMath::Pi()/180.0);

    TGeoBBox *vacbox = new TGeoBBox("vacbox", x_prime+eps, y_prime+eps, 2.*fDeltaz_view);
    TGeoBBox *vacbox_12 = new TGeoBBox("vacbox_12", x_prime_12+eps, y_prime_12+eps, 2.*fDeltaz_view);

    fFrame_material.ToLower();

    for (statnb=1;statnb<5;statnb++) {
       // tracking station loop
       TString nmstation = "Tr";
       std::stringstream ss;
       ss << statnb;
       nmstation = nmstation + ss.str();
       TGeoVolume *vac;
       TGeoVolume *vac_12;
       switch (statnb) {
	   case 1:
	      TStationz=fT1z;
              vac_12 = new TGeoVolume(nmstation, vacbox_12, med);
	      top->AddNode(vac_12, statnb, new TGeoTranslation(0,0,TStationz));
	      break;
	   case 2:
	      TStationz=fT2z;
              vac_12 = new TGeoVolume(nmstation, vacbox_12, med);
	      top->AddNode(vac_12, statnb, new TGeoTranslation(0,0,TStationz));
	      break;
	   case 3:
	      TStationz=fT3z;
              vac = new TGeoVolume(nmstation, vacbox, med);
	      top->AddNode(vac, statnb, new TGeoTranslation(0,0,TStationz));
	      break;
	   case 4:
	      TStationz=fT4z;
              vac = new TGeoVolume(nmstation, vacbox, med);
	      top->AddNode(vac, statnb, new TGeoTranslation(0,0,TStationz));
	      break;
	   default:
	      break;
       }

       if ((statnb==1)||(statnb==2)) {
          for (Int_t vnb=0; vnb<4; vnb++) {
            //view loop
	    TString nmview_12;

            Double_t angle;
            TGeoRotation r5;
	    TGeoTranslation t5;

            switch (vnb) {
	      case 0:
	        angle=0.;
	        nmview_12 = nmstation+"_x1";
	        break;
	      case 1:
	        angle=fView_angle;
	      	nmview_12 = nmstation+"_u";
	        break;
	      case 2:
	        angle=-fView_angle;
	        nmview_12 = nmstation+"_v";
	        break;
	      case 3:
	        angle=0.;
	        nmview_12 = nmstation+"_x2";
	        break;
	      default:
	        angle=0.;
	        nmview_12 = nmstation+"_x1";
            }

	    TGeoVolume *viewframe_12;
            if (fFrame_material.Contains("aluminium")) {
                viewframe_12 = new TGeoVolume(nmview_12, detcomp1_12, Al);
            }
            else {
                viewframe_12 = new TGeoVolume(nmview_12, detcomp1_12, FrameMatPtr);
            }


	    //z-translate the viewframe from station z pos
	    t5.SetTranslation(0, 0,(vnb-3./2.)*(fDeltaz_view));
	    //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)
            r5.SetAngles(angle,0,0);
            TGeoCombiTrans c5(t5, r5);
            TGeoHMatrix *h5 = new TGeoHMatrix(c5);

	    vac_12->AddNode(viewframe_12, statnb*10000000+vnb*1000000,h5);
	    viewframe_12->SetLineColor(kRed);

	    for (Int_t pnb=0; pnb<1; pnb++) {
	      //plane loop
	      TString nmplane_12 = nmview_12+"_plane_";
	      nmplane_12 += pnb;
	      TGeoBBox *plane_12 = new TGeoBBox("plane box_12", fStraw_length_12+eps/2, ftr12ydim+eps/2, planewidth/2.+3.*eps/2);
 	      TGeoVolume *planebox_12 = new TGeoVolume(nmplane_12, plane_12, med);

	      //the planebox sits in the viewframe
	      //hence z translate the plane wrt to the view
	      TGeoTranslation t3;
	      t3.SetTranslation(0, 0,(vnb-3./2.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12);
	      TGeoCombiTrans d3(t3, r5);
	      TGeoHMatrix *j3 = new TGeoHMatrix(d3);
	      vac_12->AddNode(planebox_12, statnb*10000000+vnb*1000000+pnb*100000,j3);

              for (Int_t lnb=0; lnb<2; lnb++) {

	         //width of the layer: (plane width-2*eps)/2

	         //z translate the layerbox wrt the plane box (which is already rotated)
		 TString nmlayer_12 = nmplane_12+"_layer_"; nmlayer_12 += lnb;
		 TGeoBBox *layer_12 = new TGeoBBox("layer box_12", fStraw_length_12+eps/4, ftr12ydim+eps/4, layerwidth/2.+eps/4);
		 TGeoVolume *layerbox_12 = new TGeoVolume(nmlayer_12, layer_12, med);
	         planebox_12->AddNode(layerbox_12, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12));

                 //layer loop
	         TGeoRotation r6s;
	         TGeoTranslation t6s;
                 for (Int_t snb=1; snb<fStraws_per_layer_tr12; snb++) {
                   //straw loop
	           t6s.SetTranslation(0,ftr12ydim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12,0);
                   r6s.SetAngles(90,90,0);
	           TGeoCombiTrans c6s(t6s, r6s);
                   TGeoHMatrix *h6s = new TGeoHMatrix(c6s);
	           layerbox_12->AddNode(straw_12,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb,h6s);
	           layerbox_12->AddNode(gas_12,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+2000+snb,h6s);
                   layerbox_12->AddNode(wire_12,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+3000+snb,h6s);

                 //end of straw loop
                 }
              //end of layer loop
              }
	    //end of plane loop
            }
          //end of view loop
          }
       //end of station1/2
       }
       if ((statnb==3)||(statnb==4)) {
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

	    TGeoVolume *viewframe;
            if (fFrame_material.Contains("aluminium")) {
                viewframe = new TGeoVolume(nmview, detcomp1, Al);
            }
            else {
                viewframe = new TGeoVolume(nmview, detcomp1, FrameMatPtr);
            }


	    //z-translate the viewframe from station z pos
	    t5.SetTranslation(0, 0,(vnb-3./2.)*(fDeltaz_view));
	    //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)
            r5.SetAngles(angle,0,0);
            TGeoCombiTrans c5(t5, r5);
            TGeoHMatrix *h5 = new TGeoHMatrix(c5);

	    vac->AddNode(viewframe, statnb*10000000+vnb*1000000,h5);
	    viewframe->SetLineColor(kRed);

	    for (Int_t pnb=0; pnb<1; pnb++) {
	      //plane loop
	      TString nmplane = nmview+"_plane_";
	      nmplane += pnb;
	      TGeoBBox *plane = new TGeoBBox("plane box", fStraw_length+eps/2, ftr34ydim+eps/2, planewidth/2.+3.*eps/2);
 	      TGeoVolume *planebox = new TGeoVolume(nmplane, plane, med);

	      //the planebox sits in the viewframe
	      //hence z translate the plane wrt to the view
	      TGeoTranslation t3;
	      t3.SetTranslation(0, 0,(vnb-3./2.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12);
	      TGeoCombiTrans d3(t3, r5);
	      TGeoHMatrix *j3 = new TGeoHMatrix(d3);
	      vac->AddNode(planebox, statnb*10000000+vnb*1000000+pnb*100000,j3);

              for (Int_t lnb=0; lnb<2; lnb++) {

	         //width of the layer: (plane width-2*eps)/2

	         //z translate the layerbox wrt the plane box (which is already rotated)
		 TString nmlayer = nmplane+"_layer_"; nmlayer += lnb;
		 TGeoBBox *layer = new TGeoBBox("layer box", fStraw_length+eps/4, ftr34ydim+eps/4, layerwidth/2.+eps/4);
		 TGeoVolume *layerbox = new TGeoVolume(nmlayer, layer, med);
	         planebox->AddNode(layerbox, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12));

                 //layer loop
	         TGeoRotation r6s;
	         TGeoTranslation t6s;
                 for (Int_t snb=1; snb<fStraws_per_layer_tr34; snb++) {
                   //straw loop
	           t6s.SetTranslation(0,ftr34ydim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12,0);
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
       //end of station1/2
       }


     //end of station
     }
     std::cout << "tracking stations added" << std::endl;
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
void strawtubes::StrawEndPoints(Int_t fDetectorID, TVector3 &vbot, TVector3 &vtop)
// method to get end points from TGeoNavigator
{
    Int_t statnb = fDetectorID/10000000;
    Int_t vnb =  (fDetectorID - statnb*10000000)/1000000;
    Int_t pnb =  (fDetectorID- statnb*10000000 - vnb*1000000)/100000;
    Int_t lnb =  (fDetectorID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
    TString stat = "Tr";stat+=+statnb;stat+="_";stat+=statnb;
    if (statnb==5){stat="Veto_5";}
    TString view;
    switch (vnb) {
	      case 0:
	        view = "_x1";
                if (statnb==5){view = "_x";}
	        break;
	      case 1:
	      	view = "_u";
	        break;
	      case 2:
	        view = "_v";
	        break;
	      case 3:
	        view = "_x2";
	        break;
	      default:
	        view = "_x1";}
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    TString prefix = "Tr";
    if (statnb==5){prefix="Veto";}
    else{prefix+=statnb;}
    prefix+=view;prefix+="_plane_";prefix+=pnb;prefix+="_";
    TString plane = prefix;plane+=statnb;plane+=vnb;plane+=+pnb;plane+="00000";
    TString layer = prefix+"layer_";layer+=lnb;layer+="_";layer+=statnb;layer+=vnb;layer+=pnb;layer+=lnb;layer+="0000";
    TString wire = "wire_";
    if (statnb==5){wire+="veto_";}
    wire+=(fDetectorID+1000);
    if (statnb<3){wire = "wire_12_";wire+=(fDetectorID+1000);}
    TString path = "/";path+=stat;path+="/";path+=plane;path+="/";path+=layer;path+="/";path+=wire;
    Bool_t rc = nav->cd(path);
    if (not rc){
      cout << "strawtubes::StrawDecode, TgeoNavigator failed "<<path<<endl;
      return;
    }
    TGeoNode* W = nav->GetCurrentNode();
    TGeoTube* S = dynamic_cast<TGeoTube*>(W->GetVolume()->GetShape());
    Double_t top[3] = {0,0,S->GetDZ()};
    Double_t bot[3] = {0,0,-S->GetDZ()};
    Double_t Gtop[3],Gbot[3];
    nav->LocalToMaster(top, Gtop);   nav->LocalToMaster(bot, Gbot);
    vtop.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
    vbot.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
}
void strawtubes::StrawEndPointsOriginal(Int_t detID, TVector3 &bot, TVector3 &top)
// method to get end points by emulating the geometry
{
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
  Double_t yDim = (fStraws_per_layer+1) * fStraw_pitch /2. ;
  Double_t ypos = 0.;
  Double_t xtop = 0.;
  Double_t ytop = 0.;
  Double_t xbot = 0.;
  Double_t ybot = 0.;
  if ((statnb==1)|| (statnb==2)) {
     ypos =  ftr12ydim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12;
     xtop = -fStraw_length_12*cosangle - ypos*sinangle;
     ytop = -fStraw_length_12*sinangle + ypos*cosangle;
     xbot =  fStraw_length_12*cosangle - ypos*sinangle;
     ybot =  fStraw_length_12*sinangle + ypos*cosangle;}
  if ((statnb==3)|| (statnb==4)) {
     ypos =  ftr34ydim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12;
     xtop = -fStraw_length*cosangle - ypos*sinangle;
     ytop = -fStraw_length*sinangle + ypos*cosangle;
     xbot =  fStraw_length*cosangle - ypos*sinangle;
     ybot =  fStraw_length*sinangle + ypos*cosangle; }
   if (statnb==5) {
     ypos =  fvetoydim-fStraw_pitch*snb-fOffset_plane12*pnb+lnb*fOffset_layer12;
     xtop = -fStraw_length_veto*cosangle - ypos*sinangle;
     ytop = -fStraw_length_veto*sinangle + ypos*cosangle;
     xbot =  fStraw_length_veto*cosangle - ypos*sinangle;
     ybot =  fStraw_length_veto*sinangle + ypos*cosangle; }

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
     case 5:
       TStationz = fT0z;
       break;
     default:
       TStationz = fT0z;
   }
  Double_t zpos;
  if (statnb < 5){
    zpos = TStationz+(vnb-3./2.)*fDeltaz_view+(pnb-1./2.)*fDeltaz_plane12+(lnb-1./2.)*fDeltaz_layer12;
  }else{
    zpos = TStationz+(vnb-1./2.)*fDeltaz_view+(pnb-1./2.)*fDeltaz_plane12+(lnb-1./2.)*fDeltaz_layer12;
  }
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
  //std::cout << "adding hit detid " <<detID<<std::endl;
  return new(clref[size]) strawtubesPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode, dist2Wire);
}
