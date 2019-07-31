// MufluxSpectrometer.cxx
// Magnetic Spectrometer, four tracking stations in a magnetic field.

#include "MufluxSpectrometer.h"
#include "MufluxSpectrometerPoint.h"
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

#include "TGeoNavigator.h"              //for drifttube hits
#include "TGeoNode.h"

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

#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using std::cout;
using std::endl;
using namespace ShipUnit;

MufluxSpectrometer::MufluxSpectrometer()
  : FairDetector("HighPrecisionTrackers",kTRUE, kMufluxSpectrometer),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fMufluxSpectrometerPointCollection(new TClonesArray("MufluxSpectrometerPoint"))
{
}

MufluxSpectrometer::MufluxSpectrometer(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,const char* Title)
  : FairDetector(name, Active, kMufluxSpectrometer),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fMufluxSpectrometerPointCollection(new TClonesArray("MufluxSpectrometerPoint"))
{ 
  DimX = DX;
  DimY = DY;
  DimZ = DZ;
}

MufluxSpectrometer::~MufluxSpectrometer()
{
    if (fMufluxSpectrometerPointCollection) {
        fMufluxSpectrometerPointCollection->Delete();
        delete fMufluxSpectrometerPointCollection;
    }
}

void MufluxSpectrometer::Initialize()
{
    FairDetector::Initialize();
}


// -----   Private method InitMedium 
Int_t MufluxSpectrometer::InitMedium(const char* name)
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

void MufluxSpectrometer::ChooseDetector(Bool_t muflux)
{
 fMuonFlux = muflux;
}

//Methods for Goliath by Annarita
void MufluxSpectrometer::SetGoliathSizes(Double_t H, Double_t TS, Double_t LS, Double_t BasisH)
{
    LongitudinalSize = LS;
    TransversalSize = TS;
    Height = H;
    BasisHeight = BasisH;
}

void MufluxSpectrometer::SetCoilParameters(Double_t CoilR, Double_t UpCoilH, Double_t LowCoilH, Double_t CoilD)
{
    CoilRadius = CoilR;
    UpCoilHeight = UpCoilH;
    LowCoilHeight = LowCoilH;
    CoilDistance = CoilD;
}

// Methods for drifttubes by Eric

void MufluxSpectrometer::SetTubeLength(Double_t tubelength)
{
      fTube_length = tubelength;                                     //!  Length (y) of a drift tube
}
 
void MufluxSpectrometer::SetInnerTubeDiameter(Double_t innertubediameter)
{
      fInner_Tube_diameter = innertubediameter;                      //!  Inner Tube diameter
}
 
void MufluxSpectrometer::SetOuterTubeDiameter(Double_t outertubediameter)
{
      fOuter_Tube_diameter = outertubediameter;                      //!  Outer Tube diameter
}


void MufluxSpectrometer::SetTubePitch(Double_t tubepitch)
{
      fTubes_pitch = tubepitch;                                      //!  Distance (x) between tubes in one layer
      fOffset_layer12 = 21*mm;
      fOffset_plane12 = 11*mm;
}


void MufluxSpectrometer::SetTubePitch_T1u(Double_t tubepitch_T1u, Double_t T1u_const, Double_t T1u_const_2, Double_t T1u_const_3, Double_t T1u_const_4)
{
      fTubes_pitch_T1u = tubepitch_T1u;   
      fT1u_const= T1u_const;                                 //!  Distance (x) between tubes in one layer
      fT1u_const_2= T1u_const_2; 
      fT1u_const_3= T1u_const_3; 
      fT1u_const_4= T1u_const_4; 
}

void MufluxSpectrometer::SetTubePitch_T2v(Double_t tubepitch_T2v, Double_t T2v_const, Double_t T2v_const_2, Double_t T2v_const_3, Double_t T2v_const_4)
{
      fTubes_pitch_T2v = tubepitch_T2v;   
      fT2v_const= T2v_const;                                 //!  Distance (x) between tubes in one layer
      fT2v_const_2= T2v_const_2; 
      fT2v_const_3= T2v_const_3; 
      fT2v_const_4= T2v_const_4; 
}


void MufluxSpectrometer::SetDeltazLayer(Double_t deltazlayer)
{
      fDeltaz_layer12 = deltazlayer;                                 //! Distance (z) between layer 1&2
}
 
void MufluxSpectrometer::SetDeltazPlane(Double_t deltazplane)
{
      fDeltaz_plane12 = deltazplane;                                 //! Distance (z) between plane 1&2
}
 
void MufluxSpectrometer::SetTubesPerLayer(Int_t tubesperlayer)
{
      fTubes_per_layer = tubesperlayer;                              //! number of tubes in one layer
}

void MufluxSpectrometer::SetStereoAngle(Double_t stereoangle, Double_t stereovangle)
{
      fView_angle = stereoangle;                                     //! Stereo angle of planes in a view
      fView_vangle = stereovangle;  
}

void MufluxSpectrometer::SetWireThickness(Double_t wirethickness)
{
      fWire_thickness = wirethickness;                               //! Thickness of the wire
}
 
void MufluxSpectrometer::SetDeltazView(Double_t deltazview)
{
      fDeltaz_view = deltazview;                                     //! Distance (z) between views
}
 
void MufluxSpectrometer::SetTubeLength12(Double_t tubelength12)
{
      fTube_length_12 = tubelength12;                                //! tubelength of stations 1,2
}
  
void MufluxSpectrometer::SetTr12YDim(Double_t tr12ydim)
{
      ftr12ydim = tr12ydim;   
      fTubes_per_layer_tr12= fTubes_per_layer;  
}
void MufluxSpectrometer::SetTr34YDim(Double_t tr34ydim)
{
      ftr34ydim = tr34ydim;                                          //! y size of stations 34
      fTubes_per_layer_tr34= fTubes_per_layer*4;       
}
 
void MufluxSpectrometer::SetTr12XDim(Double_t tr12xdim)
{
     ftr12xdim = tr12xdim;                                           //! x size of stations 12  
}
void MufluxSpectrometer::SetTr34XDim(Double_t tr34xdim)
{
      ftr34xdim = tr34xdim;                                          //! x size of stations 34      
}

void MufluxSpectrometer::SetDistStereo(Double_t diststereoT1,Double_t diststereoT2)
{
      fdiststereoT1 = diststereoT1;                                       //! distance between x (outside)  & u (inside) layers
      fdiststereoT2 = diststereoT2;                                       //! distance between v (inside) & x (outside)

}

void MufluxSpectrometer::SetDistT1T2(Double_t distT1T2)
{
      fdistT1T2 = distT1T2;                                       //! distance between T1&T2
}

void MufluxSpectrometer::SetDistT3T4(Double_t distT3T4)
{
      fdistT3T4 = distT3T4;                                       //! distance between T3&T4
}



void MufluxSpectrometer::SetGoliathCentre(Double_t goliathcentre_to_beam)
{
      fgoliathcentre_to_beam=goliathcentre_to_beam;
}

void MufluxSpectrometer::SetGoliathCentreZ(Double_t goliathcentre)
{
      fgoliathcentre=goliathcentre;
}

void MufluxSpectrometer::SetTStationsZ(Double_t T1z, Double_t T1x_z, Double_t T1u_z, Double_t T2z, Double_t T2v_z, Double_t T2x_z,Double_t T3z, Double_t T4z)
{
      fT1z=T1z;
      fT1x_z=T1x_z;
      fT1u_z=T1u_z;
      fT2z=T2z;
      fT2v_z=T2v_z;
      fT2x_z=T2x_z;
      fT3z=T3z;
      fT4z=T4z;
      
}

void MufluxSpectrometer::SetT3StationsZcorr(Double_t T3z_1, Double_t T3z_2, Double_t T3z_3, Double_t T3z_4)
{
      fT3z_1=T3z_1;
      fT3z_2=T3z_2;
      fT3z_3=T3z_3;
      fT3z_4=T3z_4;
}

void MufluxSpectrometer::SetT3StationsXcorr(Double_t T3x_1, Double_t T3x_2, Double_t T3x_3, Double_t T3x_4)
{
      fT3x_1=T3x_1;
      fT3x_2=T3x_2;
      fT3x_3=T3x_3;
      fT3x_4=T3x_4;
}

void MufluxSpectrometer::SetT4StationsZcorr(Double_t T4z_1, Double_t T4z_2, Double_t T4z_3, Double_t T4z_4)
{
      fT4z_1=T4z_1;
      fT4z_2=T4z_2;
      fT4z_3=T4z_3;
      fT4z_4=T4z_4;
}

void MufluxSpectrometer::SetT4StationsXcorr(Double_t T4x_1, Double_t T4x_2, Double_t T4x_3, Double_t T4x_4)
{
      fT4x_1=T4x_1;
      fT4x_2=T4x_2;
      fT4x_3=T4x_3;
      fT4x_4=T4x_4;
}


void MufluxSpectrometer::SetTStationsX(Double_t T1x_x, Double_t T1u_x, Double_t T2x_x, Double_t T2v_x, Double_t T3x, Double_t T4x)
{
      fT1x_x=T1x_x;
      fT1u_x=T1u_x;
      fT2x_x=T2x_x;
      fT2v_x=T2v_x;
      fT3x=T3x;
      fT4x=T4x;
}

void MufluxSpectrometer::SetTStationsY(Double_t T1x_y, Double_t T1u_y, Double_t T2x_y, Double_t T2v_y, Double_t T3y, Double_t T4y)
{
      fT1x_y=T1x_y;
      fT1u_y=T1u_y;
      fT2x_y=T2x_y;
      fT2v_y=T2v_y;
      fT3y=T3y;
      fT4y=T4y;
}



/* Include survey results for charm setup (added by Daniel) */
void MufluxSpectrometer::SetT3(Double_t SurveyCharm_T3x, Double_t SurveyCharm_T3y, Double_t SurveyCharm_T3z, Int_t mnb)
{
  fSurveyCharm_T3x[mnb]=SurveyCharm_T3x;
  fSurveyCharm_T3y[mnb]=SurveyCharm_T3y;;
  fSurveyCharm_T3z[mnb]=SurveyCharm_T3z;;
}

void MufluxSpectrometer::SetT4(Double_t SurveyCharm_T4x, Double_t SurveyCharm_T4y, Double_t SurveyCharm_T4z, Int_t mnb)
{
  fSurveyCharm_T4x[mnb]=SurveyCharm_T4x;
  fSurveyCharm_T4y[mnb]=SurveyCharm_T4y;;
  fSurveyCharm_T4z[mnb]=SurveyCharm_T4z;;
}


void MufluxSpectrometer::ConstructGeometry()
{ 
  gGeoManager->SetVisLevel(4);    

  InitMedium("iron");
  TGeoMedium *Fe =gGeoManager->GetMedium("iron");

  InitMedium("CoilCopper");
  TGeoMedium *Cu  = gGeoManager->GetMedium("CoilCopper");

  InitMedium("CoilAluminium");
  TGeoMedium *Al  = gGeoManager->GetMedium("CoilAluminium");
  
  //put drift tubes in air
  InitMedium("air");
  TGeoMedium *air               = gGeoManager->GetMedium("air");   

  //80% Ar, 20% CO2 gas
  InitMedium("STTmix8020_2bar");
  TGeoMedium *sttmix8020_2bar   = gGeoManager->GetMedium("STTmix8020_2bar");
  //gold plated tungsten sense wire
  InitMedium("tungsten");
  TGeoMedium *tungsten          = gGeoManager->GetMedium("tungsten");  
  
  InitMedium("ShipSens");    
  TGeoMedium *Sens =gGeoManager->GetMedium("ShipSens");   

  TGeoVolume *top = gGeoManager->GetTopVolume();
  
  gGeoManager->SetTopVisible();

  //epsilon to avoid overlapping volumes
  Double_t eps=0.05;
  Double_t epsS=0.00001;
  Double_t plate_thickness = 5.;    
  //width of view
  Double_t viewwidth = fDeltaz_view-eps;
  //width of plane
  Double_t planewidth = fOuter_Tube_diameter+fDeltaz_layer12-eps;
  //width of layer
  Double_t layerwidth = fOuter_Tube_diameter;    
  Double_t rmin, rmax;
  
  const Double_t MagneticField = 0.05 * tesla; //magnetic field; return field positive but Bdl appr 1/20
  TGeoUniformMagField *magField = new TGeoUniformMagField(0., MagneticField, 0.); //The magnetic field must be only in the vacuum space between the stations
    
  TGeoVolumeAssembly *volProva = new TGeoVolumeAssembly("volProva");   
  
 
  if (fMuonFlux){
    //***************************************************************************************************************
    //*****************************************   OPERA DRIFT TUBES BY ERIC *****************************************
    //*****************************************   Dimensions from http://www-opera.desy.de/tracker.html*************     
    //*******************************************************************************************************************  
    
    // Volume: plate

    TGeoBBox *platebox_12 = new TGeoBBox("platebox_12", ftr12xdim/2.+fTubes_pitch,  plate_thickness/2. , fDeltaz_view/2.+fTubes_pitch/2.-0.1);         
    // Volume: tube
    rmin = fInner_Tube_diameter/2.;
    rmax = fOuter_Tube_diameter/2.;
    //third argument is halflength of tube
    TGeoTube *tube_12 = new TGeoTube("tube_12",rmin,rmax,fTube_length_12/2.-2.*eps);
    TGeoVolume *drifttube_12 = new TGeoVolume("drifttube_12",tube_12, Al);
    drifttube_12->SetLineColor(4);
    drifttube_12->SetVisibility(kTRUE);
    	       	
    // Volume: gas
    rmin = fWire_thickness/2.+epsS;
    rmax = fInner_Tube_diameter/2.-epsS;
    TGeoTube *gas_tube_12 = new TGeoTube("gas_12",rmin,rmax,fTube_length_12/2.-3.*eps);
    TGeoVolume *gas_12 = new TGeoVolume("gas_12",gas_tube_12, sttmix8020_2bar);
    gas_12->SetLineColor(5);    //only the gas is sensitive
    AddSensitiveVolume(gas_12);
       
    // Volume: wire
    rmin=0.;
    rmax = fWire_thickness/2.;
    TGeoTube *wire_tube_12 = new TGeoTube("wire_12",rmin,rmax,fTube_length_12/2.-4.*eps);  
    TGeoVolume *wire_12 = new TGeoVolume("wire_12",wire_tube_12, tungsten);
    wire_12->SetLineColor(6);             

    TGeoBBox *DriftTube1 = new TGeoBBox("DriftTube1", DimX/2+ 1.*m/2, DimY/2+ 0.9*m/2, DimZ+2*cm+fdiststereoT1/2+eps); 
    TGeoVolume *volDriftTube1 = new TGeoVolume("volDriftTube1",DriftTube1,air);
    volDriftTube1->SetLineColor(kBlue-5);
  
    TGeoBBox *DriftTube2 = new TGeoBBox("DriftTube2", DimX/2+ 1.*m/2, DimY/2+ 1.*m/2, DimZ+2*cm+fdiststereoT2/2+eps);  
    TGeoVolume *volDriftTube2 = new TGeoVolume("volDriftTube2",DriftTube2,air);
    volDriftTube2->SetLineColor(kBlue-5);
            
    //Double_t xT1[4] = {-1.2*cm,1.4*cm,-0.9*cm,0.7*cm};     
    //Double_t xT2[4] = {-3.0*cm,3.12*cm,0.2*cm,-1.14*cm};  
    Double_t xT1[4] = {0.01*cm,0.*cm,0.*cm,0.*cm};     
    Double_t xT2[4] = {0.*cm,0.*cm,0.0*cm,0.*cm};  
     	    
    for (Int_t statnb=1; statnb<3; statnb++) {
      TString nmview_top_12="x";
      TString nmview_bot_12="x";
      TString nmview_12="x";
      TString nmstation="x";
      if (statnb==1) {
         volDriftTube1->SetVisibility(kFALSE);
	 top->AddNode(volDriftTube1,1,new TGeoTranslation(0,0,fT1z));
         nmstation = "Station_1"; 
	 }  
      if (statnb==2) {
         volDriftTube2->SetVisibility(kFALSE);      
	 top->AddNode(volDriftTube2,2,new TGeoTranslation(0,0,fT2z)); 
         nmstation = "Station_2";	  
	 }      
  
      for (Int_t vnb=0; vnb<2; vnb++) {
        //view loop
        Double_t angle;
        TGeoRotation r5;	
        TGeoTranslation t5;
	TGeoTranslation t6;	
	TGeoTranslation t5b;
	TGeoTranslation t6b;
	TGeoTranslation st5;
	TGeoTranslation st6;	
	TGeoTranslation st5b;
	TGeoTranslation st6b;			
        switch (vnb) {
	   case 0:
	      if (statnb==1) { 
	      	 angle=0.;
	         nmview_top_12 = nmstation+"_top_x"; 
	         nmview_bot_12 = nmstation+"_bot_x"; 
	         nmview_12 = nmstation+"_x"; 		 		 
		 }
	      if (statnb==2) { 
	      	 angle=fView_vangle;
	         nmview_top_12 = nmstation+"_top_v"; 
	         nmview_bot_12 = nmstation+"_bot_v"; 
	         nmview_12 = nmstation+"_v"; 			 		 
		 }		 
	      break;
	   case 1:
	      if (statnb==1) { 
	      	 angle=fView_angle;	 
	         nmview_top_12 = nmstation+"_top_u"; 
	         nmview_bot_12 = nmstation+"_bot_u"; 	
	         nmview_12 = nmstation+"_u"; 			 	 
		 }
	      if (statnb==2) { 
	      	 angle=0.;
	         nmview_top_12 = nmstation+"_top_x"; 
	         nmview_bot_12 = nmstation+"_bot_x"; 
	         nmview_12 = nmstation+"_x"; 		 		 
		 }
	      break;
	   default:
	      angle=0.;
        }	
	
	// aluminum plates above and below the drifttubes
	TGeoVolume *plate_top_12 = new TGeoVolume(nmview_top_12, platebox_12, Al);	 
	TGeoVolume *plate_bot_12 = new TGeoVolume(nmview_bot_12, platebox_12, Al);
	plate_top_12->SetVisibility(kTRUE);	
	plate_bot_12->SetVisibility(kTRUE);	
        plate_top_12->SetLineColor(kGreen); 	
        plate_bot_12->SetLineColor(kGreen); 
		
        r5.SetAngles(angle,0,0);
				
	//z-translate the viewframe from station z pos
	if (angle==0.) {
	    t5.SetTranslation(fT1x_x-fTubes_pitch/2.,fT1x_y+ftr12ydim/2.+eps+plate_thickness/2.+0.5*cm,(vnb-1)*fDeltaz_view);
	    t6.SetTranslation(fT1x_x-fTubes_pitch/2., fT1x_y-ftr12ydim/2.-eps-plate_thickness/2.-0.5*cm,(vnb-1)*fDeltaz_view);
	    t5b.SetTranslation(fT2x_x-fTubes_pitch/2., fT2x_y+ftr12ydim/2.+eps+plate_thickness/2.+0.5*cm,(vnb-1)*fDeltaz_view+fdiststereoT2);
	    t6b.SetTranslation(fT2x_x-fTubes_pitch/2., fT2x_y-ftr12ydim/2.-eps-plate_thickness/2.-0.5*cm,(vnb-1)*fDeltaz_view+fdiststereoT2);   
	}
        else {
	    if (statnb==1) {
            t5.SetTranslation(fT1u_x-(ftr12ydim/2.+eps+plate_thickness/2+fTubes_pitch)*sin(TMath::Pi()*angle/180.),fT1u_y+(ftr12ydim/2.+eps+plate_thickness/2)*cos(TMath::Pi()*angle/180.),fDeltaz_view+fTubes_pitch/4.);
	    t6.SetTranslation(fT1u_x+(ftr12ydim/2.+eps+plate_thickness/2)*sin(TMath::Pi()*angle/180.),fT1u_y-(ftr12ydim/2.+eps+plate_thickness/2)*cos(TMath::Pi()*angle/180.),fDeltaz_view+fTubes_pitch/4.);
	    }
	    if (statnb==2) {    
	    t5b.SetTranslation(fT2v_x-(ftr12ydim/2.+eps+plate_thickness/2+fTubes_pitch)*sin(TMath::Pi()*angle/180.),fT2v_y+(ftr12ydim/2.+eps+plate_thickness/2)*cos(TMath::Pi()*angle/180.),(vnb-1)*fDeltaz_view);
	    t6b.SetTranslation(fT2v_x+(ftr12ydim/2.+eps+plate_thickness/2)*sin(TMath::Pi()*angle/180.),fT2v_y-(ftr12ydim/2.+eps+plate_thickness/2)*cos(TMath::Pi()*angle/180.),(vnb-1)*fDeltaz_view);	     	    	    	    	    
	    }
	}
	TGeoCombiTrans c5(t5, r5);
        TGeoHMatrix *h5 = new TGeoHMatrix(c5);	
	TGeoCombiTrans c5b(t5b, r5);
        TGeoHMatrix *h5b = new TGeoHMatrix(c5b);	
        TGeoCombiTrans c6(t6, r5);
        TGeoHMatrix *h6 = new TGeoHMatrix(c6);		
        TGeoCombiTrans c6b(t6b, r5);
        TGeoHMatrix *h6b = new TGeoHMatrix(c6b);
	if (statnb==1) {
	       volDriftTube1->AddNode(plate_top_12, statnb*10+vnb,h5);
	       volDriftTube1->AddNode(plate_bot_12, statnb*10+vnb+2,h6);	   
	}
	if (statnb==2) {
	       volDriftTube2->AddNode(plate_top_12, statnb*10+vnb,h5b);
	       volDriftTube2->AddNode(plate_bot_12, statnb*10+vnb+2,h6b);	    
	 }	 
	
	//rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)	
			     
        for (Int_t pnb=0; pnb<2; pnb++) {
          //plane loop	   
          TString nmplane_12 = nmview_12+"_plane_"; 
          nmplane_12 += pnb;
          TGeoBBox *plane_12 = new TGeoBBox("plane box_12", ftr12xdim/2.+eps/2.+2*fTubes_pitch, ftr12ydim/2.+eps/2., planewidth/2.+eps/2+0.0111);	   	   
          TGeoVolume *planebox_12 = new TGeoVolume(nmplane_12, plane_12, air) ;          
	   
          //the planebox sits in the viewframe
          //hence z translate the plane wrt to the view
          TGeoTranslation t3;
	  if (statnb==1){
	    if (angle==0.){
               t3.SetTranslation(fT1x_x, fT1x_y,(vnb-1.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12);	
	    }
	    else {
	       t3.SetTranslation(fT1u_x, fT1u_y,(vnb-1.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12+fdiststereoT1);	
	    }  
	  }
	  if (statnb==2){   
	    if (angle==0.){
               t3.SetTranslation(fT2x_x, fT2x_y,(vnb-1.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12+fdiststereoT2);	
	    }
	    else {
	       t3.SetTranslation(fT2v_x, fT2v_y,(vnb-1.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12);	
	    } 	  	  	  
	  }
	    
          TGeoCombiTrans d3(t3, r5); 
          TGeoHMatrix *j3 = new TGeoHMatrix(d3);
          planebox_12->SetVisibility(kFALSE);
	  //planebox_12->SetLineColor(kRed); 	  
          if (statnb==1) {volDriftTube1->AddNode(planebox_12, statnb*10000000+vnb*1000000+pnb*100000,j3); }
          if (statnb==2) {volDriftTube2->AddNode(planebox_12, statnb*10000000+vnb*1000000+pnb*100000,j3); } 
  	
          for (Int_t lnb=0; lnb<2; lnb++) {   
            //z translate the layerbox wrt the plane box (which is already rotated)
            TString nmlayer_12 = nmplane_12+"_layer_"; nmlayer_12 += lnb;
	    TGeoBBox *layer_12 = new TGeoBBox("layer box_12", ftr12xdim/2.+2*fTubes_pitch, ftr12ydim/2., layerwidth/2.+0.011);
            TGeoVolume *layerbox_12 = new TGeoVolume(nmlayer_12, layer_12, air);	
	    layerbox_12->SetVisibility(kFALSE);	        
            if ((statnb==1 && pnb==0) && (lnb==0)) {
               planebox_12->AddNode(layerbox_12, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 
	       }	  
	    else {     
	       planebox_12->AddNode(layerbox_12, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	}
            //layer loop
            TGeoRotation r6s;	
            TGeoTranslation t6s;
            for (Int_t snb=1; snb<fTubes_per_layer_tr12+1; snb++) {
              //tubes loop
	      if ((statnb==1)&&(angle==0.)) {      	        
		 t6s.SetTranslation(xT1[lnb*1+pnb*2]-ftr12xdim/2.+fTubes_pitch*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT1x_z);}     	      
	      if ((statnb==2)&&(angle==0.)) {		     
                 t6s.SetTranslation(xT2[lnb*1+pnb*2]-ftr12xdim/2.+fTubes_pitch*(snb-1)-fOffset_plane12*pnb+fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT2x_z);} 
	      if (angle!=0.) {
	      	 if (statnb==2) {
		    if (lnb==0 && pnb==0) { t6s.SetTranslation(fT2v_const-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T2v)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT2v_z);}
		    if (lnb==1 && pnb==0) { t6s.SetTranslation(fT2v_const_2-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T2v)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT2v_z);}
		    if (lnb==0 && pnb==1) { t6s.SetTranslation(fT2v_const_3-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T2v)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT2v_z);}		    
		    if (lnb==1 && pnb==1) { t6s.SetTranslation(fT2v_const_4-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T2v)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT2v_z);}		   
                    }
	         if (statnb==1) {
                    if (lnb==0 && pnb==0) { t6s.SetTranslation(fT1u_const-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T1u)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT1u_z);}
		    if (lnb==1 && pnb==0) { t6s.SetTranslation(fT1u_const_2-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T1u)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT1u_z);}
		    if (lnb==0 && pnb==1) { t6s.SetTranslation(fT1u_const_3-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T1u)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT1u_z);}		    
		    if (lnb==1 && pnb==1) { t6s.SetTranslation(fT1u_const_4-ftr12xdim/2.+(fTubes_pitch+fTubes_pitch_T1u)*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,fT1u_z);}		   
		    } 
	      }	 
		 	      
	      r6s.SetAngles(0,90,90);
              TGeoCombiTrans c6s(t6s, r6s);
              TGeoHMatrix *h6s = new TGeoHMatrix(c6s);
              layerbox_12->AddNode(drifttube_12,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb,h6s);
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
    } //end of statnb loop             
 }   
    else{ //station positions for charm measurement
    }

    
    //***********************************************************************************************
    //*****************************************   GOLIATH BY ANNARITA *****************************************
    //***********************************************************************************************
    
    TGeoBBox *BoxGoliath = new TGeoBBox(TransversalSize/2,Height/2,LongitudinalSize/2);
    TGeoVolume *volGoliath = new TGeoVolume("volGoliath",BoxGoliath,air);
    TGeoRotation ry90;	
    TGeoTranslation gtrans;

    ry90.RotateY(90);
    //From latest (2017) field measurements: beam coordinates x=-1.4mm, y=-178.6mm, hence need to move Goliath up
    //gtrans.SetTranslation(1.4*mm,fgoliathcentre_to_beam,350.75);
    //edms 1834065 v.1 :
    gtrans.SetTranslation(1.4*mm,fgoliathcentre_to_beam-0.75*cm,fgoliathcentre);
    TGeoCombiTrans cg(gtrans,ry90);
    TGeoHMatrix *mcg = new TGeoHMatrix(cg);

    top->AddNode(volGoliath,1,mcg); 


    //
    //******* UPPER AND LOWER BASE *******
    //
    
    TGeoBBox *Base = new TGeoBBox(TransversalSize/2,BasisHeight/2,LongitudinalSize/2);
    TGeoVolume *volBase = new TGeoVolume("volBase",Base,Fe);
    volBase->SetLineColor(kRed);
    volGoliath->AddNode(volBase,1,new TGeoTranslation(0, Height/2 - BasisHeight/2, 0)); //upper part
    volGoliath->AddNode(volBase,2,new TGeoTranslation(0, -Height/2 + BasisHeight/2, 0)); //lower part
    
    //
    //**************************** MAGNETS ******************************
    //
    
    TGeoRotation *r1 = new TGeoRotation();
    r1->SetAngles(0,90,0);
    TGeoCombiTrans t1(0, Height/2 - BasisHeight - UpCoilHeight/2, 0,r1);
    TGeoHMatrix *m1 = new TGeoHMatrix(t1);
    
    TGeoTube *magnetUp = new TGeoTube(0,CoilRadius,UpCoilHeight/2);
    TGeoVolume *volmagnetUp = new TGeoVolume("volmagnetUp",magnetUp,Cu);
    volmagnetUp->SetLineColor(kGreen);
    volGoliath->AddNode(volmagnetUp,1,m1); //upper part
    
    
    TGeoCombiTrans t2(0, -Height/2 + BasisHeight + LowCoilHeight/2, 0,r1);
    TGeoHMatrix *m_2 = new TGeoHMatrix(t2);
    
    
    TGeoTube *magnetDown = new TGeoTube(0,CoilRadius,LowCoilHeight/2);
    TGeoVolume *volmagnetDown = new TGeoVolume("volmagnetDown",magnetDown,Al);
    volmagnetDown->SetLineColor(kGreen);
    volGoliath->AddNode(volmagnetDown,1,m_2); //lower part
    
    //
    //********************* LATERAL SURFACES ****************************
    //
    
    Double_t base1 = 135, base2 = 78; //basis of the trapezoid
    Double_t side1 = 33, side2 = 125, side3 = 57, side4 = 90; //Sides of the columns
    
    //***** SIDE Left Front ****
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1 = new TGeoBBox("LateralS1",side1/2,UpCoilHeight/2,base1/2);
    TGeoTranslation *tr1 = new TGeoTranslation(-TransversalSize/2 + side1/2, Height/2 - BasisHeight - UpCoilHeight/2, -LongitudinalSize/2 + base1/2);
    TGeoVolume *volLateralS1 = new TGeoVolume("volLateralS1",LateralS1,Fe);
    volLateralS1->SetLineColor(kRed);
    //volLateralS1->SetField(magField);    
    volGoliath->AddNode(volLateralS1, 1, tr1);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2 = new TGeoArb8("LateralS2", UpCoilHeight/2);
    LateralS2->SetVertex(0, side4, 0);
    LateralS2->SetVertex(1, side1, 0);
    LateralS2->SetVertex(2, side1, base1);
    LateralS2->SetVertex(3, side4, base2);
    LateralS2->SetVertex(4, side4, 0);
    LateralS2->SetVertex(5, side1, 0);
    LateralS2->SetVertex(6, side1, base1);
    LateralS2->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2 = new TGeoVolume("volLateralS2",LateralS2,Fe);
    volLateralS2->SetLineColor(kRed);
    //volLateralS2->SetField(magField);   
     
    TGeoRotation *r2 = new TGeoRotation();
    r2->SetAngles(0,90,0);
    TGeoCombiTrans tr3(-TransversalSize/2, Height/2 - BasisHeight - UpCoilHeight/2, -LongitudinalSize/2,r2);
    TGeoHMatrix *m3_a = new TGeoHMatrix(tr3);
    volGoliath->AddNode(volLateralS2, 1, m3_a);
    
    
    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoBBox *LateralSurface1low = new TGeoBBox("LateralSurface1low",side1/2,(CoilDistance + LowCoilHeight)/2,side2/2);
    TGeoVolume *volLateralSurface1low = new TGeoVolume("volLateralSurface1low",LateralSurface1low,Fe);
    volLateralSurface1low->SetLineColor(kRed);
    //volLateralSurface1low->SetField(magField);    
    TGeoTranslation *tr1low = new TGeoTranslation(-TransversalSize/2 +side1/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, -LongitudinalSize/2 + side2/2);
    volGoliath->AddNode(volLateralSurface1low, 1, tr1low);;
    
    
    //SHORTER RECTANGLE
    TGeoBBox *LateralSurface2low = new TGeoBBox("LateralSurface2low",side3/2,(CoilDistance + LowCoilHeight)/2,base2/2);
    TGeoVolume *volLateralSurface2low = new TGeoVolume("volLateralSurface2low",LateralSurface2low,Fe);
    volLateralSurface2low->SetLineColor(kRed);
    TGeoTranslation *tr2low = new TGeoTranslation(-TransversalSize/2 +side1 + side3/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, -LongitudinalSize/2 + base2/2);
    volGoliath->AddNode(volLateralSurface2low, 1, tr2low);
    //volLateralSurface2low->SetField(magField);  
      
    //***** SIDE Right Front ****
    
    //LONGER RECTANGLE
    TGeoTranslation *tr1_b = new TGeoTranslation(-TransversalSize/2 + side1/2, Height/2 - BasisHeight - UpCoilHeight/2, LongitudinalSize/2 - base1/2);
    TGeoVolume *volLateralS1_b = new TGeoVolume("volLateralS1_b",LateralS1,Fe);
    volLateralS1_b->SetLineColor(kRed);
    //volLateralS1_b->SetField(magField);    
    volGoliath->AddNode(volLateralS1_b, 1, tr1_b);
    
    //TRAPEZOID
    TGeoArb8 *LateralS2_b = new TGeoArb8("LateralS2_b",UpCoilHeight/2);
    LateralS2_b ->SetVertex(0, side4, 0);
    LateralS2_b ->SetVertex(1, side1, 0);
    LateralS2_b ->SetVertex(2, side1, base1);
    LateralS2_b ->SetVertex(3, side4, base2);
    LateralS2_b ->SetVertex(4, side4, 0);
    LateralS2_b ->SetVertex(5, side1, 0);
    LateralS2_b ->SetVertex(6, side1, base1);
    LateralS2_b ->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2_b = new TGeoVolume("volLateralS2_b",LateralS2_b,Fe);
    volLateralS2_b->SetLineColor(kRed);
    //volLateralS2_b->SetField(magField); 
       
    TGeoRotation *r2_b = new TGeoRotation();
    r2_b->SetAngles(0,270,0);
    TGeoCombiTrans tr2_b(-TransversalSize/2 , Height/2 - BasisHeight - UpCoilHeight/2, LongitudinalSize/2,r2_b);
    TGeoHMatrix *m3_b = new TGeoHMatrix(tr2_b);
    volGoliath->AddNode(volLateralS2_b, 1, m3_b);
    
    
    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoVolume *volLateralSurface1blow = new TGeoVolume("volLateralSurface1blow",LateralSurface1low,Fe);
    volLateralSurface1blow->SetLineColor(kRed);
    //volLateralSurface1blow->SetField(magField);
    TGeoTranslation *tr1blow = new TGeoTranslation(-TransversalSize/2 +side1/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, LongitudinalSize/2 - side2/2);
    volGoliath->AddNode(volLateralSurface1blow, 1, tr1blow);;
    
    
    //SHORTER RECTANGLE
    TGeoVolume *volLateralSurface2blow = new TGeoVolume("volLateralSurface2blow",LateralSurface2low,Fe);
    volLateralSurface2blow->SetLineColor(kRed);
    //volLateralSurface2blow->SetField(magField);
    TGeoTranslation *tr2blow = new TGeoTranslation(-TransversalSize/2 +side1 + side3/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, LongitudinalSize/2 - base2/2);
    volGoliath->AddNode(volLateralSurface2blow, 1, tr2blow);
    
    
    //***** SIDE left Back ****
    
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_d = new TGeoBBox("LateralS1_d",side1/2,(UpCoilHeight + LowCoilHeight + CoilDistance)/2,base1/2);
    TGeoTranslation *tr1_d = new TGeoTranslation(TransversalSize/2 - side1/2, Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, -LongitudinalSize/2 + base1/2);
    TGeoVolume *volLateralS1_d = new TGeoVolume("volLateralS1_d",LateralS1_d,Fe);
    volLateralS1_d->SetLineColor(kRed);
    //volLateralS1_d->SetField(magField);    
    volGoliath->AddNode(volLateralS1_d, 1, tr1_d);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_d = new TGeoArb8("LateralS2_d",(UpCoilHeight + LowCoilHeight + CoilDistance)/2);
    LateralS2_d->SetVertex(0, side4, 0);
    LateralS2_d->SetVertex(1, side1, 0);
    LateralS2_d->SetVertex(2, side1, base1);
    LateralS2_d->SetVertex(3, side4, base2);
    LateralS2_d->SetVertex(4, side4, 0);
    LateralS2_d->SetVertex(5, side1, 0);
    LateralS2_d->SetVertex(6, side1, base1);
    LateralS2_d->SetVertex(7, side4, base2);
    
    
    TGeoVolume *volLateralS2_d = new TGeoVolume("volLateralS2_d",LateralS2_d,Fe);
    volLateralS2_d->SetLineColor(kRed);
    //volLateralS2_d->SetField(magField);    
    
    TGeoRotation *r2_d = new TGeoRotation();
    r2_d->SetAngles(0,270,180);
    TGeoCombiTrans tr2_d(TransversalSize/2 , Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, -LongitudinalSize/2,r2_d);
    TGeoHMatrix *m3_d = new TGeoHMatrix(tr2_d);
    volGoliath->AddNode(volLateralS2_d, 1, m3_d);
    
    
    //***** SIDE right Back ****
    
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_c = new TGeoBBox("LateralS1_c",side1/2,(UpCoilHeight + LowCoilHeight + CoilDistance)/2,base1/2);
    TGeoTranslation *tr1_c = new TGeoTranslation(TransversalSize/2 - side1/2, Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, LongitudinalSize/2 - base1/2);
    TGeoVolume *volLateralS1_c = new TGeoVolume("volLateralS1_c",LateralS1_c,Fe);
    volLateralS1_c->SetLineColor(kRed);
    //volLateralS1_c->SetField(magField);      
    volGoliath->AddNode(volLateralS1_c, 1, tr1_c);
  
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_c = new TGeoArb8("LateralS2_c",(UpCoilHeight + LowCoilHeight + CoilDistance)/2);
    LateralS2_c ->SetVertex(0, side4, 0);
    LateralS2_c ->SetVertex(1, side1, 0);
    LateralS2_c ->SetVertex(2, side1, base1);
    LateralS2_c ->SetVertex(3, side4, base2);
    LateralS2_c ->SetVertex(4, side4, 0);
    LateralS2_c ->SetVertex(5, side1, 0);
    LateralS2_c ->SetVertex(6, side1, base1);
    LateralS2_c ->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2_c = new TGeoVolume("volLateralS2_c",LateralS2_c,Fe);
    volLateralS2_c->SetLineColor(kRed);
    //volLateralS2_c->SetField(magField);
        
    TGeoRotation *r2_c = new TGeoRotation();
    r2_c->SetAngles(0,90,180);
    TGeoCombiTrans tr2_c(TransversalSize/2 , Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, LongitudinalSize/2,r2_c);
    TGeoHMatrix *m3_c = new TGeoHMatrix(tr2_c);
    volGoliath->AddNode(volLateralS2_c, 1, m3_c);

    //END GOLIATH PART BY ANNARITA
    
      //detectors for muonflux downstream of Goliath 
      // Volume: tube
      rmin = fInner_Tube_diameter/2.;
      rmax = fOuter_Tube_diameter/2.;
      //third argument is halflength of tube
      TGeoTube *tube = new TGeoTube("tube",rmin,rmax,fTube_length/2.-4.*eps);
      TGeoVolume *drifttube = new TGeoVolume("drifttube",tube, Al);
      drifttube->SetLineColor(4);
      drifttube->SetVisibility(kTRUE);   
      
      //short tubes needed for charm
      TGeoTube *short_tube = new TGeoTube("short_tube",rmin,rmax,1.1/1.6*fTube_length/2.-4.*eps);
      TGeoVolume *short_drifttube = new TGeoVolume("short_drifttube",short_tube, Al);
      short_drifttube->SetLineColor(4);
      short_drifttube->SetVisibility(kTRUE);  
      
      // Volume: gas
      rmin = fWire_thickness/2.+epsS;
      rmax = fInner_Tube_diameter/2.-epsS;

      TGeoTube *gas_tube = new TGeoTube("gas_tube",rmin,rmax,fTube_length/2.-6.*eps);
      TGeoVolume *gas = new TGeoVolume("gas",gas_tube, sttmix8020_2bar);
      gas->SetLineColor(5);    //only the gas is sensitive
      AddSensitiveVolume(gas);

      /* short tubes for charm added by daniel */
      TGeoTube *short_gas_tube = new TGeoTube("short_gas_tube",rmin,rmax,1.1/1.6*fTube_length/2.-6.*eps);
      TGeoVolume *short_gas = new TGeoVolume("short_gas",short_gas_tube, sttmix8020_2bar);
      short_gas->SetLineColor(5);    //only the gas is sensitive
      AddSensitiveVolume(short_gas);
      
       
      // Volume: wire
      rmin=0.;
      rmax = fWire_thickness/2.;
      TGeoTube *wire_tube = new TGeoTube("wire_tube",rmin,rmax,fTube_length/2.-8.*eps);
      TGeoVolume *wire = new TGeoVolume("wire",wire_tube, tungsten);
      wire->SetLineColor(6);

      /* short wires added for charm by daniel */
      TGeoTube *short_wire_tube = new TGeoTube("short_wire_tube",rmin,rmax,1.1/1.6*fTube_length/2.-8.*eps);
      TGeoVolume *short_wire = new TGeoVolume("short_wire",short_wire_tube, tungsten);
      short_wire->SetLineColor(6);  
      
      //Double_t xT3[4] = {-0.9*cm,1.14*cm,-0.8*cm,1.1*cm};    
      //Double_t xT4[4] = {0.8*cm,1.29*cm,0.15*cm,2.0*cm}; 
      Double_t xT3[4] = {0.*cm,0.*cm,0.*cm,0.*cm};    
      Double_t xT4[4] = {0.*cm,0.*cm,0.*cm,0.*cm}; 
      Double_t Tz_translation;
      Double_t Tx_translation;

      if (fMuonFlux){
	
	for (Int_t statnb=3; statnb<5; statnb++) {
	  
	  //TGeoBBox *platebox_34 = new TGeoBBox("platebox_34", ftr34xdim/2.+1.+2*fTubes_pitch,  plate_thickness/2. , fDeltaz_view/2.);
	  TGeoBBox *platebox_34 = new TGeoBBox("platebox_34", ftr34xdim/2.+fTubes_pitch/2.,  plate_thickness/2. , fDeltaz_view/2.);   
	  
	  TGeoBBox *DriftTube3 = new TGeoBBox("DriftTube3", DimX/2 + 1*m/2 , DimY/2 + 0.68*m/2, DimZ/2+eps); 
	  TGeoVolume *volDriftTube3 = new TGeoVolume("volDriftTube3",DriftTube3,air);
	  volDriftTube3->SetLineColor(kBlue-5);
	  
	  TGeoBBox *DriftTube4 = new TGeoBBox("DriftTube4", DimX/2 + 1*m/2, DimY/2 + 0.68*m/2 , DimZ/2+eps); 
	  TGeoVolume *volDriftTube4 = new TGeoVolume("volDriftTube4",DriftTube4,air);
	  volDriftTube4->SetLineColor(kBlue-5);
	  Int_t vnb=0;
	  TString nmview_34="x";
	  TString nmview_top_34="x";
	  TString nmview_bot_34="x";
	  if (statnb==3) {
	    volDriftTube3->SetVisibility(kFALSE);
	    //move drifttubes up so they cover the Goliath aperture, not centered on the beam
	    top->AddNode(volDriftTube3,3,new TGeoTranslation(fT3x,fT3y+fgoliathcentre_to_beam,fT3z));
	    nmview_34 = "Station_3_x";
	    nmview_top_34="Station_3_top_x";
	    nmview_bot_34="Station_3_bot_x";	 
	    
	  }  
	  if (statnb==4) {
	    volDriftTube4->SetVisibility(kFALSE);     
	    //move drifttubes up so they cover the Goliath aperture, not centered on the beam
	    top->AddNode(volDriftTube4,4,new TGeoTranslation(fT4x,fT4y+fgoliathcentre_to_beam,fT4z));
	    nmview_34 = "Station_4_x";
	    nmview_top_34="Station_4_top_x";
	    nmview_bot_34="Station_4_bot_x";		  	  	  
	  }  
	  
	  TGeoRotation r5;	
	  TGeoTranslation t5; 
	  TGeoTranslation t6; 	  
	  Double_t angle=0.;	    	
	  
	  TGeoVolume *plate_top_34 = new TGeoVolume(nmview_top_34, platebox_34, Al);	 
	  TGeoVolume *plate_bot_34 = new TGeoVolume(nmview_bot_34, platebox_34, Al);
	  
	  plate_top_34->SetVisibility(kTRUE);	
	  plate_bot_34->SetVisibility(kTRUE);	
	  plate_top_34->SetLineColor(kGreen); 	
	  plate_bot_34->SetLineColor(kGreen); 
	  
	  t5.SetTranslation(0, fTube_length/2.+eps+plate_thickness/2+0.5*cm,0.);
	  t6.SetTranslation(0, -fTube_length/2.-eps-plate_thickness/2-0.5*cm,0.);
	  //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)	
	  r5.SetAngles(angle,0,0);
	  TGeoCombiTrans c5(t5, r5);
	  TGeoHMatrix *h5 = new TGeoHMatrix(c5);	
	  TGeoCombiTrans c6(t6, r5);
	  TGeoHMatrix *h6 = new TGeoHMatrix(c6);	      
	  
	  //viewframe_34->SetVisibility(kFALSE);	
	  if (statnb==3) {
	    volDriftTube3->AddNode(plate_top_34, statnb*10+vnb,h5);
	    volDriftTube3->AddNode(plate_bot_34, statnb*10+vnb+2,h6);
	  }
	  if (statnb==4) {
	    volDriftTube4->AddNode(plate_top_34, statnb*10+vnb,h5);
	    volDriftTube4->AddNode(plate_bot_34, statnb*10+vnb+2,h6);       
	  }
	  
          
	  for (Int_t pnb=0; pnb<2; pnb++) {
	    //plane loop	   
	    TString nmplane_34 = nmview_34+"_plane_"; 
	    nmplane_34 += pnb;
	    TGeoBBox *plane_34 = new TGeoBBox("plane box_34", ftr34xdim/2.+eps/2.+2*fTubes_pitch, ftr34ydim/2+eps/2., planewidth/2.+eps/2+0.137);	   	   
	    TGeoVolume *planebox_34 = new TGeoVolume(nmplane_34, plane_34, air) ;          
	    
	    //the planebox sits in the viewframe
	    //hence z translate the plane wrt to the view
	    
	    TGeoTranslation t3;
	    
	    t3.SetTranslation(0, 0,(pnb-1./2.)*fDeltaz_plane12);
	    TGeoCombiTrans d3(t3, r5); 
	    TGeoHMatrix *j3 = new TGeoHMatrix(d3);
	    planebox_34->SetVisibility(kFALSE);	  
	    if (statnb==3) {volDriftTube3->AddNode(planebox_34, statnb*10000000+vnb*1000000+pnb*100000,j3); }
	    if (statnb==4) {volDriftTube4->AddNode(planebox_34, statnb*10000000+vnb*1000000+pnb*100000,j3); }   
	    
	    for (Int_t lnb=0; lnb<2; lnb++) {   
	      
	      //z translate the layerbox wrt the plane box (which is already rotated)
	      TString nmlayer_34 = nmplane_34+"_layer_"; nmlayer_34 += lnb;
	      TGeoBBox *layer_34 = new TGeoBBox("layer box_34", ftr34xdim/2.+2*fTubes_pitch, ftr34ydim/2., layerwidth/2.+0.136);
	      TGeoVolume *layerbox_34 = new TGeoVolume(nmlayer_34, layer_34, air);	
	      layerbox_34->SetVisibility(kFALSE);	        
	      planebox_34->AddNode(layerbox_34, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  
	      
	      //layer loop
	      TGeoRotation r6s;	
	      TGeoTranslation t6s;
	      for (Int_t snb=1; snb<fTubes_per_layer_tr34+1; snb++) {
		//tubes loop
		if (statnb==3){	
		  if ((snb>0) && (snb<13))  { 
		    Tz_translation = fT3z_1;
		    Tx_translation = fT3x_1;		      
		  }	
		  if ((snb>12) && (snb<25)) {
		    Tz_translation = fT3z_2;
		    Tx_translation = fT3x_2;		      
		  } 
		  if ((snb>24) && (snb<37)) { 
		    Tz_translation = fT3z_3;
		    Tx_translation = fT3x_3;		      
		  }	
		  if ((snb>36) && (snb<49)) { 
		    Tz_translation = fT3z_4;
		    Tx_translation = fT3x_4;		      
		  }        	      
		  t6s.SetTranslation(Tx_translation+xT3[pnb*2+lnb*1]-ftr34xdim/2.+fTubes_pitch*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,Tz_translation); }
		if (statnb==4){	
		  if ((snb>0) && (snb<13))  { 
		    Tz_translation = fT4z_1;
		    Tx_translation = fT4x_1;		      
		  }	
		  if ((snb>12) && (snb<25)) {
		    Tz_translation = fT4z_2;
		    Tx_translation = fT4x_2;		      
		  } 
		  if ((snb>24) && (snb<37)) { 
		    Tz_translation = fT4z_3;
		    Tx_translation = fT4x_3;		      
		  }	
		  if ((snb>36) && (snb<49)) { 
		    Tz_translation = fT4z_4;
		    Tx_translation = fT4x_4;		      
		  }           	      	                
		  t6s.SetTranslation(Tx_translation+xT4[pnb*2+lnb*1]-ftr34xdim/2.+fTubes_pitch*(snb-1)-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),0,Tz_translation); }
		
		r6s.SetAngles(0,90,90);
		TGeoCombiTrans c6s(t6s, r6s);
		TGeoHMatrix *h6s = new TGeoHMatrix(c6s);
		layerbox_34->AddNode(drifttube,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb,h6s);
		layerbox_34->AddNode(gas,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+2000+snb,h6s);
		layerbox_34->AddNode(wire,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+3000+snb,h6s);  
		//end of straw loop
	      }
	      //end of layer loop
	    }
	    //end of plane loop		
	  }	
	} //end of statnb loop  
	
      }
      
      
      else {
	//define a center of the stations for the bounding box
	//there are four modules + the top module. The center is placed in between

	double zcenter_t3=0;
	double zcenter_t4=0;

	for(int mnb=0;mnb<4;mnb++){
	  zcenter_t3+=fSurveyCharm_T3z[mnb];
	  zcenter_t4+=fSurveyCharm_T4z[mnb];
	}

	zcenter_t3=(zcenter_t3/4+fSurveyCharm_T3z[4])/2;
	zcenter_t4=(zcenter_t4/4+fSurveyCharm_T4z[4])/2;

	double zcenter_t34=(zcenter_t3+zcenter_t4)/2;
	double distance_t34=zcenter_t4-zcenter_t3;

	
	TGeoBBox *DriftTubeCharm = new TGeoBBox("DriftTubeCharm", 1.15*m/2, 2.5*m/2, distance_t34/2+eps+22.5*cm); 
	TGeoVolume *volDriftTubeCharm = new TGeoVolume("volDriftTubeCharm",DriftTubeCharm,air);
	volDriftTubeCharm->SetLineColor(kBlue-5);
	
	volDriftTubeCharm->SetVisibility(kFALSE);
	top->AddNode(volDriftTubeCharm,1,new TGeoTranslation(0,0,zcenter_t34));
	
	for (Int_t statnb=3; statnb<5; statnb++) {
	  for(Int_t mnb=0;mnb<5;mnb++){	    
	    //plateboxes need to be adapted for charm (individual small plates, taking dimensions from t12)
	    TGeoBBox *platebox = new TGeoBBox("platebox", ftr12xdim/2.+fTubes_pitch/2.,  plate_thickness/2. , fDeltaz_view/2.);   
	    
	    //view number?
	    Int_t vnb=0;
	    TString nmview_34="x";
	    TString nmview_top_34="x";
	    TString nmview_bot_34="x";
	    
	    if (statnb==3) {
	      nmview_top_34="Station_3_top_x_module";
	      nmview_bot_34="Station_3_bot_x_module";	 
	      
	    }  
	    if (statnb==4) {
	      nmview_top_34="Station_4_top_x_module";
	      nmview_bot_34="Station_4_bot_x_module";		  	  	  
	    }  
	    
	    nmview_top_34+=mnb;
	    nmview_bot_34+=mnb;
	    

	    TGeoRotation r5;	
	    TGeoTranslation t5; 
	    TGeoTranslation t6; 	  
	    Double_t angle=0.;	    	
	    
	    TGeoVolume *plate_top_34 = new TGeoVolume(nmview_top_34, platebox, Al);	 
	    TGeoVolume *plate_bot_34 = new TGeoVolume(nmview_bot_34, platebox, Al);
	    
	    plate_top_34->SetVisibility(kTRUE);	
	    plate_bot_34->SetVisibility(kTRUE);	
	    plate_top_34->SetLineColor(kGreen); 	
	    plate_bot_34->SetLineColor(kGreen); 
	    
	    if (statnb==3) {
	      t5.SetTranslation(fSurveyCharm_T3x[mnb], fSurveyCharm_T3y[mnb]+fTube_length/2.+eps+plate_thickness/2+0.5*cm,fSurveyCharm_T3z[mnb]-zcenter_t34);
	      t6.SetTranslation(fSurveyCharm_T3x[mnb], fSurveyCharm_T3y[mnb]-fTube_length/2.-eps-plate_thickness/2-0.5*cm,fSurveyCharm_T3z[mnb]-zcenter_t34);
	      if(mnb==4){
		t5.SetTranslation(fSurveyCharm_T3x[mnb], fSurveyCharm_T3y[mnb]+1.1/1.6*fTube_length/2.+eps+plate_thickness/2+0.5*cm,fSurveyCharm_T3z[mnb]-zcenter_t34);
		t6.SetTranslation(fSurveyCharm_T3x[mnb], fSurveyCharm_T3y[mnb]+1.1/1.6*-fTube_length/2.-eps-plate_thickness/2-0.5*cm,fSurveyCharm_T3z[mnb]-zcenter_t34);
	      }
	    }
	    if (statnb==4) {
	      t5.SetTranslation(fSurveyCharm_T4x[mnb], fSurveyCharm_T4y[mnb]+fTube_length/2.+eps+plate_thickness/2+0.5*cm,fSurveyCharm_T4z[mnb]-zcenter_t34);
	      t6.SetTranslation(fSurveyCharm_T4x[mnb], fSurveyCharm_T4y[mnb]-fTube_length/2.-eps-plate_thickness/2-0.5*cm,fSurveyCharm_T4z[mnb]-zcenter_t34);
	      if(mnb==4){
		t5.SetTranslation(fSurveyCharm_T4x[mnb], fSurveyCharm_T4y[mnb]+1.1/1.6*fTube_length/2.+eps+plate_thickness/2+0.5*cm,fSurveyCharm_T4z[mnb]-zcenter_t34);
		t6.SetTranslation(fSurveyCharm_T4x[mnb], fSurveyCharm_T4y[mnb]+1.1/1.6*-fTube_length/2.-eps-plate_thickness/2-0.5*cm,fSurveyCharm_T4z[mnb]-zcenter_t34);
	      }
	    }

	    //rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)	
	    r5.SetAngles(angle,0,0);
	    TGeoCombiTrans c5(t5, r5);
	    TGeoHMatrix *h5 = new TGeoHMatrix(c5);	
	    TGeoCombiTrans c6(t6, r5);
	    TGeoHMatrix *h6 = new TGeoHMatrix(c6);	      

	    volDriftTubeCharm->AddNode(plate_top_34, statnb*10+mnb,h5);
	    volDriftTubeCharm->AddNode(plate_bot_34, statnb*10+mnb*2,h6);

	    for (Int_t pnb=0; pnb<2; pnb++) {
	      //plane loop	   
	      TString nmplane_34 = nmview_34+"_station_"; 
	      nmplane_34 += statnb;
	      nmplane_34 += "_plane_";
	      nmplane_34 += pnb;
	      nmplane_34 += "_module_";
	      nmplane_34 += mnb;
	      TGeoBBox *plane_34 = new TGeoBBox("plane box_34", ftr12xdim/2.+eps/2.+2*fTubes_pitch, ftr34ydim/2+eps/2., planewidth/2.+eps/2);	   	   
	      TGeoVolume *planebox_34 = new TGeoVolume(nmplane_34, plane_34, air) ;          
	      
	      //the planebox sits in the viewframe
	      //hence z translate the plane wrt to the view
	      
	      TGeoTranslation t3;
	      
	      t3.SetTranslation(0, 0,(pnb-1./2.)*fDeltaz_plane12);
	      TGeoCombiTrans d3(t3, r5); 
	      TGeoHMatrix *j3 = new TGeoHMatrix(d3);
	      planebox_34->SetVisibility(kFALSE);	  

	      volDriftTubeCharm->AddNode(planebox_34, mnb*100000000+statnb*10000000+vnb*1000000+pnb*100000,j3); 
	      
	      for (Int_t lnb=0; lnb<2; lnb++) {   
		
		//z translate the layerbox wrt the plane box (which is already rotated)
		TString nmlayer_34 = nmplane_34+"_layer_"; nmlayer_34 += lnb;
		TGeoBBox *layer_34 = new TGeoBBox("layer box_34", ftr12xdim/2.+2*fTubes_pitch, ftr34ydim/2., layerwidth/2.);
		TGeoVolume *layerbox_34 = new TGeoVolume(nmlayer_34, layer_34, air);	
		layerbox_34->SetVisibility(kFALSE);	        
		planebox_34->AddNode(layerbox_34, mnb*100000000+statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  
		
		//layer loop
		TGeoRotation r6s;	
		TGeoTranslation t6s;
		for (Int_t snb=1; snb<fTubes_per_layer_tr12+1; snb++) {
		  //tubes loop
		  if (statnb==3){		      	      
		    t6s.SetTranslation(fSurveyCharm_T3x[mnb]+fTubes_pitch*(snb-1)-225.5*mm-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),fSurveyCharm_T3y[mnb],fSurveyCharm_T3z[mnb]-zcenter_t34); }
		  if (statnb==4){	       	      	                
		    t6s.SetTranslation(fSurveyCharm_T4x[mnb]+fTubes_pitch*(snb-1)-225.5*mm-fOffset_plane12*(pnb-1)-fOffset_layer12*(pnb*lnb+(pnb-1)*(lnb-1)),fSurveyCharm_T4y[mnb],fSurveyCharm_T4z[mnb]-zcenter_t34); }
		  
		  r6s.SetAngles(0,90,90);
		  TGeoCombiTrans c6s(t6s, r6s);
		  TGeoHMatrix *h6s = new TGeoHMatrix(c6s);
		  if(mnb==4){
		    layerbox_34->AddNode(short_drifttube,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+snb+12*mnb,h6s);
		    layerbox_34->AddNode(short_gas,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+2000+snb+12*mnb,h6s);
		    layerbox_34->AddNode(short_wire,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+3000+snb+12*mnb,h6s);
		  }
		  else{
		    layerbox_34->AddNode(drifttube,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+1000+12*mnb+snb,h6s);
		    layerbox_34->AddNode(gas,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+2000+12*mnb+snb,h6s);
		    layerbox_34->AddNode(wire,statnb*10000000+vnb*1000000+pnb*100000+lnb*10000+3000+12*mnb+snb,h6s);
		  }
		  //end of straw loop
		}
		//end of layer loop
	      }
	      //end of plane loop
	    }
	  }//end of mnb loop
	} //end of statnb loop  
	  
	
      }
	

}

Bool_t  MufluxSpectrometer::ProcessHits(FairVolume* vol)
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
    if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       ||
        gMC->IsTrackDisappeared()   ) {
        if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();	
	
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
        Int_t tube_uniqueId;

        gMC->CurrentVolID(tube_uniqueId);
        if (fVolumeID == tube_uniqueId) {
             //std::cout << pdgCode<< " same volume again ? "<< tube_uniqueId << " exit:" << gMC->IsTrackExiting() << " stop:" << gMC->IsTrackStop() << " disappeared:" << gMC->IsTrackDisappeared()<< std::endl;
              return kTRUE; }	      
        fVolumeID = tube_uniqueId;
	//std::cout<< " tube_uniqueId "<<tube_uniqueId<<std::endl;	  
        // # d = |pq . u x v|/|u x v|
        TVector3 bot,top;	  
        TubeEndPoints(tube_uniqueId,bot,top);
	  
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
        AddHit(fTrackID, tube_uniqueId, TVector3(xmean, ymean,  zmean),
        TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, deltaTrackLength,	   
        fELoss,pdgCode,dist2Wire);
        if (dist2Wire>2.23){
             std::cout << "addhit " << dist2Wire<< " tube id " << tube_uniqueId << " pdgcode " << pdgCode<< " dot prod " << pq.Dot(uCrossv)<< std::endl;
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

        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(kMufluxSpectrometer);
    }
    
    return kTRUE;
}

void MufluxSpectrometer::EndOfEvent()
{
    fMufluxSpectrometerPointCollection->Clear();
}


void MufluxSpectrometer::Register()
{
    
    /** This will create a branch in the output tree called
     MufluxSpectrometerPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("MufluxSpectrometerPoint", "MufluxSpectrometer",
                                          fMufluxSpectrometerPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------
// -----   returns hpt, arm, rpc numbers -----------------------------------
void MufluxSpectrometer::DecodeVolumeID(Int_t detID,int &nHPT)
{
  nHPT = detID;
}

TClonesArray* MufluxSpectrometer::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fMufluxSpectrometerPointCollection; }
    else { return NULL; }
}

void MufluxSpectrometer::Reset()
{
    fMufluxSpectrometerPointCollection->Clear();
}

// -----   Public method Spectrometer Decode    -------------------------------------------
// -----   returns station layer ... numbers -----------------------------------
void MufluxSpectrometer::TubeDecode(Int_t detID,int &statnb,int &vnb,int &pnb,int &lnb, int &snb)
{
  statnb = detID/10000000;
  vnb =  (detID - statnb*10000000)/1000000;
  pnb =  (detID - statnb*10000000 - vnb*1000000)/100000;
  lnb =  (detID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
  snb =   detID - statnb*10000000 - vnb*1000000 - pnb*100000 - lnb*10000 - 2000;
}

// -----   Public method TubeEndPoints    -------------------------------------------
// -----   returns top and bottom coordinate of tube  -----------------------------------
void MufluxSpectrometer::TubeEndPoints(Int_t fDetectorID, TVector3 &vbot, TVector3 &vtop)
{
// method to get end points from TGeoNavigator

  Int_t statnb = fDetectorID/10000000;
  Int_t vnb =  (fDetectorID - statnb*10000000)/1000000;
  Int_t pnb =  (fDetectorID - statnb*10000000 - vnb*1000000)/100000;
  Int_t lnb =  (fDetectorID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
  TString stat = "volDriftTube";stat+=+statnb;stat+="_";stat+=statnb;
  TString view;
  switch (vnb) {
     case 0:
       if (statnb==1) {view = "_x";}
       if (statnb==2) {view = "_v";}  
       if (statnb==3) {view = "_x";}
       if (statnb==4) {view = "_x";}             
       break;
     case 1:
       if (statnb==1) { view = "_u";}
       if (statnb==2) { view = "_x";}       
       break;     
     default:
       view = "_x";
   }   
   TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
   TString prefix = "Station_";
   prefix+=statnb;
   prefix+=view;prefix+="_plane_";prefix+=pnb;prefix+="_";
   TString plane = prefix;plane+=statnb;plane+=vnb;plane+=+pnb;plane+="00000";
   TString layer = prefix+"layer_";layer+=lnb;layer+="_";layer+=statnb;layer+=vnb;layer+=pnb;layer+=lnb;layer+="0000";
   TString wire = "wire_";
   wire+=(fDetectorID+1000);
   if (statnb<3){wire = "wire_12_";wire+=(fDetectorID+1000);}
   TString path = "";path+="/";path+=stat;path+="/";path+=plane;path+="/";path+=layer;path+="/";path+=wire;
      
   Bool_t rc = nav->cd(path);
   if (not rc){
       cout << "MufluxSpectrometer::TubeEndPoints, TGeoNavigator failed "<<path<<endl; 
       return;
   }  
   TGeoNode* W = nav->GetCurrentNode();
   TGeoTube* S = dynamic_cast<TGeoTube*>(W->GetVolume()->GetShape());
   Double_t top[3] = {0,0,S->GetDZ()};
   Double_t bot[3] = {0,0,-S->GetDZ()};
   Double_t Gtop[3],Gbot[3];
   nav->LocalToMaster(top, Gtop);
   nav->LocalToMaster(bot, Gbot);
   vtop.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);   
   vbot.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);  
}
MufluxSpectrometerPoint* MufluxSpectrometer::AddHit(Int_t trackID, Int_t detID,
                        TVector3 pos, TVector3 mom,
                        Double_t time, Double_t length,
					    Double_t eLoss, Int_t pdgCode, Double_t dist2Wire)

{
    TClonesArray& clref = *fMufluxSpectrometerPointCollection;
    Int_t size = clref.GetEntriesFast();

    return new(clref[size]) MufluxSpectrometerPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode,
    dist2Wire);
}


ClassImp(MufluxSpectrometer)
