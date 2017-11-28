// MufluxSpectrometer.cxx
// Magnetic Spectrometer, four tracking stations in a magnetic field.

#include "MufluxSpectrometer.h"
//#include "MagneticSpectrometer.h" 
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

#include "TGeoUniformMagField.h"
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

void MufluxSpectrometer::SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox)
{
  SBoxX = SX;
  SBoxY = SY;
  SBoxZ = SZ;
  zBoxPosition = zBox;
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

void MufluxSpectrometer::SetStereoAngle(Int_t stereoangle)
{
      fView_angle = stereoangle;                                     //! Stereo angle of planes in a view
      fcosphi=cos(TMath::Pi()*(90.-fView_angle)/180.);
      fsinphi=sin(TMath::Pi()*(90.-fView_angle)/180.);
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
 
void MufluxSpectrometer::SetVacBox_x(Double_t vacbox_x)
{
      fVacBox_x = vacbox_x;                                          //! x size of station vacuum box
}
 
void MufluxSpectrometer::SetVacBox_y(Double_t vacbox_y)
{
      fVacBox_y = vacbox_y;                                          //! y size of station vacuum box
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


void MufluxSpectrometer::ConstructGeometry()
{ 
  gGeoManager->SetVisLevel(4);
    
  InitMedium("vacuum");
  TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");

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
  Double_t eps=0.0001;
  Double_t epsS=0.00001;
  Double_t plate_thickness = 5.;    
  //width of view
  Double_t viewwidth = fDeltaz_view-eps;
  //width of plane
  Double_t planewidth = fOuter_Tube_diameter+fDeltaz_layer12-eps;
  //width of layer
  Double_t layerwidth = fOuter_Tube_diameter;    
  Double_t rmin, rmax;
  
  const Double_t MagneticField = 1 * tesla; //magnetic field
  TGeoUniformMagField *magfield = new TGeoUniformMagField(0., MagneticField, 0.); //The magnetic field must be only in the vacuum space between the stations

  TGeoBBox *ProvaBox = new TGeoBBox("ProvaBox", 0. , 0., 0.);  
  TGeoVolume *volProva = new TGeoVolume("volProva", ProvaBox, vacuum);   
  
  Double_t z[4] = {0.,0.,0.,0.}; 
    
 
    //***************************************************************************************************************
    //*****************************************   OPERA DRIFT TUBES BY ERIC *****************************************
    //*****************************************   Dimensions from https://www-opera.desy.de/tracker.html*************     
    //*******************************************************************************************************************  
    
    // Volume: plate

    TGeoBBox *platebox_12 = new TGeoBBox("platebox_12", ftr12xdim/2.+1.+2*fTubes_pitch,  plate_thickness/2. , fDeltaz_view/2.);    
             
    // Volume: tube
    rmin = fInner_Tube_diameter/2.;
    rmax = fOuter_Tube_diameter/2.;
    //third argument is halflength of tube
    TGeoTube *tube_12 = new TGeoTube("tube_12",rmin,rmax,fTube_length_12/2.-4.*eps);
    TGeoVolume *drifttube_12 = new TGeoVolume("drifttube_12",tube_12, Al);
    drifttube_12->SetLineColor(4);
    drifttube_12->SetVisibility(kTRUE);
    	       	
    // Volume: gas
    rmin = fWire_thickness/2.+epsS;
    rmax = fInner_Tube_diameter/2.-epsS;
    TGeoTube *gas_tube_12 = new TGeoTube("gas_12",rmin,rmax,fTube_length_12/2.-6.*eps);
    TGeoVolume *gas_12 = new TGeoVolume("gas_12",gas_tube_12, sttmix8020_2bar);
    gas_12->SetLineColor(5);    //only the gas is sensitive
    AddSensitiveVolume(gas_12);
       
    // Volume: wire
    rmin=0.;
    rmax = fWire_thickness/2.;
    TGeoTube *wire_tube_12 = new TGeoTube("wire_12",rmin,rmax,fTube_length_12/2.-8.*eps);  
    TGeoVolume *wire_12 = new TGeoVolume("wire_12",wire_tube_12, tungsten);
    wire_12->SetLineColor(6);             

    TGeoBBox *DriftTube1 = new TGeoBBox("DriftTube1", DimX/2+ 1*m/2, DimY/2+ 1*m/2, DimZ+eps); 
    TGeoVolume *volDriftTube1 = new TGeoVolume("volDriftTube1",DriftTube1,air);
    volDriftTube1->SetLineColor(kBlue-5);
  
    TGeoBBox *DriftTube2 = new TGeoBBox("DriftTube2", DimX/2+ 1*m/2, DimY/2+ 1*m/2, DimZ+eps);  
    TGeoVolume *volDriftTube2 = new TGeoVolume("volDriftTube2",DriftTube2,air);
    volDriftTube2->SetLineColor(kBlue-5);
        
    z[0] = 5.1*cm + 2.*DimZ;
    z[1] = 85.1*cm + 2.*DimZ;
    z[2] = 4.5*m +86*cm + 4 * DimZ + 3.*cm;
    z[3] = 4.5*m + 286*cm + 4 * DimZ + 3.*cm; //with SA and SB    
    //Double_t z[4] = {5.1*cm + 2.*DimZ, 85.1*cm + 2.*DimZ, 4.5*m +86*cm + 4 * DimZ, 4.5*m + 286*cm + 4 * DimZ }; //with SA
    //Double_t z[4] = {5.1*cm + 2.*DimZ, 120.1*cm + 2.*DimZ, 4.5*m +121*cm + 4 * DimZ, 4.5*m + 321*cm + 4 * DimZ }; //with SA    
    //Double_t z[4] = {2.*DimZ, 100*cm + 2.*DimZ, 4.5*m +100*cm + 4 * DimZ, 4.5*m + 300*cm + 4 * DimZ }; 
    //Double_t z[4] = {2.*DimZ, 50*cm + 2.*DimZ, 4.5*m +50*cm + 4 * DimZ, 4.5*m + 150*cm + 4 * DimZ };    
    //relative distances (80 cm between T1,T2; 200 cm between T3,T4) (after implementation of Goliath)
		    
    for (Int_t statnb=1; statnb<3; statnb++) {
      TString nmview_top_12="x";
      TString nmview_bot_12="x";
      TString nmview_12="x";
      TString nmstation="x";
      if (statnb==1) {
         volDriftTube1->SetVisibility(kFALSE);
	 top->AddNode(volDriftTube1,1,new TGeoTranslation(0,0,DimZ+5.1*cm));
         nmstation = "Station_1"; 
	 }  
      if (statnb==2) {
         volDriftTube2->SetVisibility(kFALSE);      
	 top->AddNode(volDriftTube2,2,new TGeoTranslation(0,0,85.1*cm + DimZ)); //with SA
         nmstation = "Station_2";	  
	 }      
  
      for (Int_t vnb=0; vnb<2; vnb++) {
        //view loop
        Double_t angle;
        TGeoRotation r5;	
        TGeoTranslation t5;
	TGeoTranslation t6;			
        switch (vnb) {
	   case 0:
	      if (statnb==1) { 
	      	 angle=0.;
	         nmview_top_12 = nmstation+"_top_x"; 
	         nmview_bot_12 = nmstation+"_bot_x"; 
	         nmview_12 = nmstation+"_x"; 		 		 
		 }
	      if (statnb==2) { 
	      	 angle=fView_angle;
	         nmview_top_12 = nmstation+"_top_u"; 
	         nmview_bot_12 = nmstation+"_bot_u"; 
	         nmview_12 = nmstation+"_v"; 			 		 
		 }		 
	      break;
	   case 1:
	      if (statnb==1) { 
	      	 angle=-fView_angle;	 
	         nmview_top_12 = nmstation+"_top_v"; 
	         nmview_bot_12 = nmstation+"_bot_v"; 	
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
		
	//z-translate the viewframe from station z pos
	t5.SetTranslation(0, ftr12ydim/2.+eps+plate_thickness/2.+0.5*cm,(2*vnb-1)*fDeltaz_view/2);
	t6.SetTranslation(0, -ftr12ydim/2.-eps-plate_thickness/2.-0.5*cm,(2*vnb-1)*fDeltaz_view/2);
	//rotate the frame box by angle degrees around the z axis (0 if it isn't a stereo view)	
        r5.SetAngles(angle,0,0);
        TGeoCombiTrans c5(t5, r5);
        TGeoHMatrix *h5 = new TGeoHMatrix(c5);	
        TGeoCombiTrans c6(t6, r5);
        TGeoHMatrix *h6 = new TGeoHMatrix(c6);	
		
	if (statnb==1) {
	    volDriftTube1->AddNode(plate_top_12, statnb*10+vnb,h5);
	    volDriftTube1->AddNode(plate_bot_12, statnb*10+vnb+2,h6);	   
	    }
	if (statnb==2) {
	    volDriftTube2->AddNode(plate_top_12, statnb*10+vnb,h5);
	    volDriftTube2->AddNode(plate_bot_12, statnb*10+vnb+2,h6);	    
	    }
			     
        for (Int_t pnb=0; pnb<2; pnb++) {
          //plane loop	   
          TString nmplane_12 = nmview_12+"_plane_"; 
          nmplane_12 += pnb;
          TGeoBBox *plane_12 = new TGeoBBox("plane box_12", ftr12xdim/2.+eps/2.+fTubes_pitch, ftr12ydim/2.+eps/2., planewidth/2.+eps/2);	   	   
          TGeoVolume *planebox_12 = new TGeoVolume(nmplane_12, plane_12, air) ;          
	   
          //the planebox sits in the viewframe
          //hence z translate the plane wrt to the view
          TGeoTranslation t3;
          t3.SetTranslation(0, 0,(vnb-1./2.)*(fDeltaz_view)+(pnb-1./2.)*fDeltaz_plane12);	  		
          TGeoCombiTrans d3(t3, r5); 
          TGeoHMatrix *j3 = new TGeoHMatrix(d3);
          planebox_12->SetVisibility(kFALSE);
	  //planebox_12->SetLineColor(kRed); 	  
          if (statnb==1) {volDriftTube1->AddNode(planebox_12, statnb*10000000+vnb*1000000+pnb*100000,j3); }
          if (statnb==2) {volDriftTube2->AddNode(planebox_12, statnb*10000000+vnb*1000000+pnb*100000,j3); } 
  	
          for (Int_t lnb=0; lnb<2; lnb++) {   
            //z translate the layerbox wrt the plane box (which is already rotated)
            TString nmlayer_12 = nmplane_12+"_layer_"; nmlayer_12 += lnb;
            TGeoBBox *layer_12 = new TGeoBBox("layer box_12", ftr12xdim/2.+eps/4+fTubes_pitch, ftr12ydim/2.+eps/4, layerwidth/2.+eps/4);
            TGeoVolume *layerbox_12 = new TGeoVolume(nmlayer_12, layer_12, air);	
	    layerbox_12->SetVisibility(kFALSE);	        
            planebox_12->AddNode(layerbox_12, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  
	
            //layer loop
            TGeoRotation r6s;	
            TGeoTranslation t6s;
            for (Int_t snb=1; snb<fTubes_per_layer_tr12+1; snb++) {
              //tubes loop
	      t6s.SetTranslation(ftr12xdim/2.-fTubes_pitch*(snb-1)+fOffset_plane12*pnb-lnb*fOffset_layer12,0,0); 
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
     
    TGeoBBox *VacuumBox = new TGeoBBox("VacuumBox", TransversalSize/2, 90*cm/2., (175 * cm)/2.);
    //TGeoVolume *volVacuum = new TGeoVolume("VolVacuum", VacuumBox, vacuum);
    TGeoVolume *volVacuum = new TGeoVolume("VolVacuum", VacuumBox, air);
    volVacuum->SetVisibility(0);
    volVacuum->SetField(magfield);
    volVacuum->SetLineColor(kYellow);

    
      //***********************************************************************************************
    //*****************************************   GOLIATH BY ANNARITA *****************************************
    //***********************************************************************************************
    //    Double_t MagneticField = 1*tesla;
    
    TGeoUniformMagField *magField1 = new TGeoUniformMagField(0.,-MagneticField,0.); //magnetic field in Goliath pillars
    
    TGeoBBox *BoxGoliath = new TGeoBBox(TransversalSize/2,Height/2,LongitudinalSize/2);
    TGeoVolume *volGoliath = new TGeoVolume("volGoliath",BoxGoliath,vacuum);
    //volProva->AddNode(volGoliath,1,new TGeoTranslation(0,0,-SBoxZ/2 + z[1] + LongitudinalSize/2));  
    
    //Goliath raised by 17cm
    top->AddNode(volGoliath,1,new TGeoTranslation(0,17*cm,zBoxPosition-SBoxZ/2 + z[1] + LongitudinalSize/2)); 
    volGoliath->AddNode(volVacuum, 1, new TGeoTranslation(0,-5 * cm,0)); //commented to insert the new Goliath 

    //
    //******* UPPER AND LOWER BASE *******
    //
    
    TGeoBBox *Base = new TGeoBBox(TransversalSize/2,BasisHeight/2,LongitudinalSize/2);
    TGeoVolume *volBase = new TGeoVolume("volBase",Base,Fe);
    volBase->SetLineColor(kRed);
    //volBase->SetTransparency(7);
    volGoliath->AddNode(volBase,1,new TGeoTranslation(0, Height/2 - BasisHeight/2, 0)); //upper part
    volGoliath->AddNode(volBase,2,new TGeoTranslation(0, -Height/2 + BasisHeight/2, 0)); //lower part
    
    //
    //**************************** MAGNETS ******************************
    //
    
    TGeoRotation *r1 = new TGeoRotation();
    r1->SetAngles(0,90,0);
    TGeoCombiTrans t1(0, Height/2 - BasisHeight - UpCoilHeight/2, 0,r1);
    //t1.Print();
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
    volLateralS1->SetField(magField1);
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
    volLateralS2->SetField(magField1);
    
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
    volLateralSurface1low->SetField(magField1);
    TGeoTranslation *tr1low = new TGeoTranslation(-TransversalSize/2 +side1/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, -LongitudinalSize/2 + side2/2);
    volGoliath->AddNode(volLateralSurface1low, 1, tr1low);;
    
    
    //SHORTER RECTANGLE
    TGeoBBox *LateralSurface2low = new TGeoBBox("LateralSurface2low",side3/2,(CoilDistance + LowCoilHeight)/2,base2/2);
    TGeoVolume *volLateralSurface2low = new TGeoVolume("volLateralSurface2low",LateralSurface2low,Fe);
    volLateralSurface2low->SetLineColor(kRed);
    TGeoTranslation *tr2low = new TGeoTranslation(-TransversalSize/2 +side1 + side3/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, -LongitudinalSize/2 + base2/2);
    volGoliath->AddNode(volLateralSurface2low, 1, tr2low);
    volLateralSurface2low->SetField(magField1);
    
    //***** SIDE Right Front ****
    
    //LONGER RECTANGLE
    TGeoTranslation *tr1_b = new TGeoTranslation(-TransversalSize/2 + side1/2, Height/2 - BasisHeight - UpCoilHeight/2, LongitudinalSize/2 - base1/2);
    TGeoVolume *volLateralS1_b = new TGeoVolume("volLateralS1_b",LateralS1,Fe);
    volLateralS1_b->SetLineColor(kRed);
    volLateralS1_b->SetField(magField1);
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
    volLateralS2_b->SetField(magField1);
    
    TGeoRotation *r2_b = new TGeoRotation();
    r2_b->SetAngles(0,270,0);
    TGeoCombiTrans tr2_b(-TransversalSize/2 , Height/2 - BasisHeight - UpCoilHeight/2, LongitudinalSize/2,r2_b);
    TGeoHMatrix *m3_b = new TGeoHMatrix(tr2_b);
    volGoliath->AddNode(volLateralS2_b, 1, m3_b);
    
    
    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoVolume *volLateralSurface1blow = new TGeoVolume("volLateralSurface1blow",LateralSurface1low,Fe);
    volLateralSurface1blow->SetLineColor(kRed);
    volLateralSurface1blow->SetField(magField1);
    TGeoTranslation *tr1blow = new TGeoTranslation(-TransversalSize/2 +side1/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, LongitudinalSize/2 - side2/2);
    volGoliath->AddNode(volLateralSurface1blow, 1, tr1blow);;
    
    
    //SHORTER RECTANGLE
    TGeoVolume *volLateralSurface2blow = new TGeoVolume("volLateralSurface2blow",LateralSurface2low,Fe);
    volLateralSurface2blow->SetLineColor(kRed);
    volLateralSurface2blow->SetField(magField1);
    TGeoTranslation *tr2blow = new TGeoTranslation(-TransversalSize/2 +side1 + side3/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, LongitudinalSize/2 - base2/2);
    volGoliath->AddNode(volLateralSurface2blow, 1, tr2blow);
    
    
    //***** SIDE left Back ****
    
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_d = new TGeoBBox("LateralS1_d",side1/2,(UpCoilHeight + LowCoilHeight + CoilDistance)/2,base1/2);
    TGeoTranslation *tr1_d = new TGeoTranslation(TransversalSize/2 - side1/2, Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, -LongitudinalSize/2 + base1/2);
    TGeoVolume *volLateralS1_d = new TGeoVolume("volLateralS1_d",LateralS1_d,Fe);
    volLateralS1_d->SetLineColor(kRed);
    volLateralS1_d->SetField(magField1);
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
    volLateralS2_d->SetField(magField1);
    
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
        volLateralS1_c->SetField(magField1);
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
    volLateralS2_c->SetField(magField1);
    
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
    
      // Volume: gas
      rmin = fWire_thickness/2.+epsS;
      rmax = fInner_Tube_diameter/2.-epsS;

      TGeoTube *gas_tube = new TGeoTube("gas",rmin,rmax,fTube_length/2.-6.*eps);
      TGeoVolume *gas = new TGeoVolume("gas",gas_tube, sttmix8020_2bar);
      gas->SetLineColor(5);    //only the gas is sensitive
      AddSensitiveVolume(gas);
       
      // Volume: wire
      rmin=0.;
      rmax = fWire_thickness/2.;
      TGeoTube *wire_tube = new TGeoTube("wire",rmin,rmax,fTube_length/2.-8.*eps);
      TGeoVolume *wire = new TGeoVolume("wire",wire_tube, tungsten);
      wire->SetLineColor(6);    

      for (Int_t statnb=3; statnb<5; statnb++) {
    
        TGeoBBox *platebox_34 = new TGeoBBox("platebox_34", ftr34xdim/2.+1.+2*fTubes_pitch,  plate_thickness/2. , fDeltaz_view/2.);
    
        TGeoBBox *DriftTube3 = new TGeoBBox("DriftTube3", DimX/2 + 1*m/2 , DimY/2 + 1*m/2, DimZ/2+eps); 
        TGeoVolume *volDriftTube3 = new TGeoVolume("volDriftTube3",DriftTube3,air);
        volDriftTube3->SetLineColor(kBlue-5);

        TGeoBBox *DriftTube4 = new TGeoBBox("DriftTube4", DimX/2 + 1*m/2, DimY/2 + 1*m/2 , DimZ/2+eps); 
        TGeoVolume *volDriftTube4 = new TGeoVolume("volDriftTube4",DriftTube4,air);
        volDriftTube4->SetLineColor(kBlue-5);
        Int_t vnb=0;
        TString nmview_34="x";
        TString nmview_top_34="x";
        TString nmview_bot_34="x";
        if (statnb==3) {
          volDriftTube3->SetVisibility(kFALSE);
	  top->AddNode(volDriftTube3,3,new TGeoTranslation(0,0,4.5*m +86*cm + 2.5 * DimZ + 3.*cm));//with SA and SB
          nmview_34 = "Station_3_x";
	  nmview_top_34="Station_3_top_x";
	  nmview_bot_34="Station_3_bot_x";	 
	 	 
	}  
        if (statnb==4) {
          volDriftTube4->SetVisibility(kFALSE);     
	  top->AddNode(volDriftTube4,4,new TGeoTranslation(0,0,4.5*m +286*cm + 2.5 * DimZ + 3.*cm)); //with SA and SB
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
          TGeoBBox *plane_34 = new TGeoBBox("plane box_34", ftr34xdim/2.+eps/2.+fTubes_pitch, ftr34ydim/2+eps/2., planewidth/2.+eps/2);	   	   
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
           TGeoBBox *layer_34 = new TGeoBBox("layer box_34", ftr34xdim/2.+eps/4.+fTubes_pitch, ftr34ydim/2.+eps/4., layerwidth/2.+eps/4.);
           TGeoVolume *layerbox_34 = new TGeoVolume(nmlayer_34, layer_34, air);	
	   layerbox_34->SetVisibility(kFALSE);	        
           planebox_34->AddNode(layerbox_34, statnb*10000000+vnb*1000000+pnb*100000+lnb*10000,new TGeoTranslation(0,0,(lnb-1./2.)*fDeltaz_layer12)); 	  
	
           //layer loop
           TGeoRotation r6s;	
           TGeoTranslation t6s;
           for (Int_t snb=1; snb<fTubes_per_layer_tr34+1; snb++) {
              //tubes loop
	      t6s.SetTranslation(ftr34xdim/2.-fTubes_pitch*(snb-1)+fOffset_plane12*pnb-lnb*fOffset_layer12,0,0); 
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
   TString wire = "gas_";
   wire+=(fDetectorID);
   if (statnb<3){wire = "gas_12_";wire+=(fDetectorID);}
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
   vtop.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
   vbot.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
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
