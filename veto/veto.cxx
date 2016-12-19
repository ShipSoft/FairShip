#include "veto.h"
#include <math.h>
#include "vetoPoint.h"

#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
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
#include "TGeoEltu.h"
#include "TGeoSphere.h"
#include "TGeoBoolNode.h"
#include "TGeoCompositeShape.h"
#include "TGeoShapeAssembly.h"
#include "TGeoTube.h"
#include "TGeoArb8.h"
#include "TGeoCone.h"
#include "TGeoMaterial.h"
#include "TParticle.h"



#include <iostream>
using std::cout;
using std::endl;

Double_t cm  = 1;       // cm
Double_t m   = 100*cm;  //  m
Double_t mm  = 0.1*cm;  //  mm

veto::veto()
  : FairDetector("veto", kTRUE, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fvetoPointCollection(new TClonesArray("vetoPoint"))
{
}

veto::veto(const char* name, Bool_t active)
  : FairDetector(name, active, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fFastMuon(kFALSE),
    fT0z(-2390.),              //!  z-position of veto station
    fT1z(1510.),               //!  z-position of tracking station 1
    fT2z(1710.),               //!  z-position of tracking station 2
    fT3z(2150.),               //!  z-position of tracking station 3
    fT4z(2370.),               //!  z-position of tracking station 4
    f_InnerSupportThickness(3.*cm),    //!  inner support thickness of decay volume
    f_OuterSupportThickness(8.*mm),    //!  outer support thickness of decay volume
    f_VetoThickness(0.3*m), 	//!  thickness of liquid or plastic scintillator
    zFocusX(-80*m),              //! focus point for x dimension, given by muon free envelope
    zFocusY(-80*m),              //! focus point for Y dimension
    ws(0.5*m),                  //! Straw screen plates sticking out of the outer tube.
    fXstart(1.5*m),             //! horizontal width at start of decay volume
    fYstart(1.5*m),             //! vertical width at start of decay volume
    fvetoPointCollection(new TClonesArray("vetoPoint")),
    vetoMed_name("Scintillator"),   // for liquid scintillator
    supportMedIn_name("steel"),        // for vacuum option
    supportMedOut_name("Aluminum"),    // for vacuum option
    ribMed_name("steel"),
    f_RibThickness(3.*cm),
    decayVolumeMed_name("vacuums")    // for vacuum option
{
}

veto::~veto()
{
  if (fvetoPointCollection) {
    fvetoPointCollection->Delete();
    delete fvetoPointCollection;
  }
}

void veto::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  vetoGeoPar* par=(vetoGeoPar*)(rtdb->getContainer("vetoGeoPar"));
}
// private method make trapezoids with hole and rounded corners
TGeoVolume* veto::GeoTrapezoid(TString xname,Double_t thick,Double_t dz,Double_t dx_start,Double_t dy_start,Double_t slopeX,Double_t slopeY,Double_t dcorner,Int_t colour,TGeoMedium *material,Bool_t sens=kFALSE)
{

      TString nm = xname.ReplaceAll("-","");  //otherwise it will try to subtract "-" in TGeoComposteShape
      Double_t dy1 = dy_start;
      Double_t dy2 = dy_start;
      if(slopeY>0){dy2 = dy1 + 2*slopeY*dz;}
      Double_t dx1 = dx_start;
      Double_t dx2 = dx1;
      if(slopeX>0){dx2=dx1+2*slopeX*dz;}
      Double_t exr=(dy2-dy1)/2.+(dx2-dx1)/2.;
      Double_t dc1=dcorner-exr/2.;
      Double_t dc2=dcorner+exr/2.;
      Double_t dxm=(dx1+dx2)/2.;
      Double_t dym=(dy1+dy2)/2.;
      
      TGeoArb8 *T2 = new TGeoArb8("T2"+nm,dz);
      Double_t tdx1 = dxm-exr/2.;
      Double_t tdx2 = dxm+exr/2.;
      Double_t tdy1 = dym-exr/2.;
      Double_t tdy2 = dym+exr/2.;
      T2->SetVertex(0,-tdx1,-tdy1);
      T2->SetVertex(1,-tdx1,tdy1);
      T2->SetVertex(2,tdx1,tdy1);
      T2->SetVertex(3,tdx1,-tdy1);
      T2->SetVertex(4,-tdx2,-tdy2);
      T2->SetVertex(5,-tdx2,tdy2);
      T2->SetVertex(6,tdx2,tdy2);
      T2->SetVertex(7,tdx2,-tdy2);
      TGeoVolume *T;
      if (thick>0){ 
       //dcorner is the distance between the center of corner
       //circle and the inner edge of the object.
       tdx1 = dxm-exr/2.-thick;
       tdx2 = dxm+exr/2.-thick;
       tdy1 = dym-exr/2.-dc1+0.1*cm;
       tdy2 = dym+exr/2.-dc2+0.1*cm;
       TGeoArb8 *T1 = new TGeoArb8("T1"+nm,dz+1.E-6);
       T1->SetVertex(0,-tdx1,-tdy1);
       T1->SetVertex(1,-tdx1,tdy1);
       T1->SetVertex(2,tdx1,tdy1);
       T1->SetVertex(3,tdx1,-tdy1);
       T1->SetVertex(4,-tdx2,-tdy2);
       T1->SetVertex(5,-tdx2,tdy2);
       T1->SetVertex(6,tdx2,tdy2);
       T1->SetVertex(7,tdx2,-tdy2);

       tdx1 = dxm-exr/2.-dc1+0.1*cm;
       tdx2 = dxm+exr/2.-dc2+0.1*cm;
       tdy1 = dym-thick-exr/2.;
       tdy2 = dym-thick+exr/2.;
       TGeoArb8 *T3 = new TGeoArb8("T3"+nm,dz+2.E-6);
       T3->SetVertex(0,-tdx1,-tdy1);
       T3->SetVertex(1,-tdx1,tdy1);
       T3->SetVertex(2,tdx1,tdy1);
       T3->SetVertex(3,tdx1,-tdy1);
       T3->SetVertex(4,-tdx2,-tdy2);
       T3->SetVertex(5,-tdx2,tdy2);
       T3->SetVertex(6,tdx2,tdy2);
       T3->SetVertex(7,tdx2,-tdy2);

       //now subtract the corners using TGeoConeSeg
       TGeoConeSeg *Ci1 = new TGeoConeSeg("Ci1"+nm,dz+3.e-1,0.,dc1,0.,dc2,-1.,91.);
       TGeoTranslation *t1 = new TGeoTranslation("t1"+nm,dxm-dcorner-thick,dym-dcorner-thick,0.);
       t1->RegisterYourself();
       TGeoConeSeg *Co1 = new TGeoConeSeg("Co1"+nm,dz+3.e-1,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,-1.,91.);

       TGeoConeSeg *Ci2 = new TGeoConeSeg("Ci2"+nm,dz+3.e-1,0.,dc1,0.,dc2,89.,181.);
       TGeoTranslation *t2 = new TGeoTranslation("t2"+nm,-dxm+dcorner+thick,dym-dcorner-thick,0.);
       t2->RegisterYourself();
       TGeoConeSeg *Co2 = new TGeoConeSeg("Co2"+nm,dz+3.e-1,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,89.,181.);

       TGeoConeSeg *Ci3 = new TGeoConeSeg("Ci3"+nm,dz+3.e-1,0.,dc1,0.,dc2,179.,271.);
       TGeoTranslation *t3 = new TGeoTranslation("t3"+nm,-dxm+dcorner+thick,-dym+dcorner+thick,0.);
       t3->RegisterYourself();
       TGeoConeSeg *Co3 = new TGeoConeSeg("Co3"+nm,dz+3.e-1,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,179.,271.);

       TGeoConeSeg *Ci4 = new TGeoConeSeg("Ci4"+nm,dz+3.e-1,0.,dc1,0.,dc2,269.,361.);
       TGeoTranslation *t4 = new TGeoTranslation("t4"+nm,dxm-dcorner-thick,-dym+dcorner+thick,0.);
       t4->RegisterYourself();
       TGeoConeSeg *Co4 = new TGeoConeSeg("Co4"+nm,dz+3.e-1,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,269.,361.);

       TGeoCompositeShape *T213 = new TGeoCompositeShape("T213"+nm,"T2"+nm+"-T1"+nm+"-T3"+nm+\
                                                         "-Ci1"+nm+":t1"+nm+"-Co1"+nm+":t1"+nm+\
                                                         "-Ci2"+nm+":t2"+nm+"-Co2"+nm+":t2"+nm+\
                                                         "-Ci3"+nm+":t3"+nm+"-Co3"+nm+":t3"+nm+\
                                                         "-Ci4"+nm+":t4"+nm+"-Co4"+nm+":t4"+nm);

       T = new TGeoVolume(xname, T213, material);
       
      } else {
       //only cut outer corners off
       //now subtract the corners using TGeoConeSeg
       TGeoTranslation *t1 = new TGeoTranslation("t1"+nm,dxm-dcorner-thick,dym-dcorner-thick,0.);
       t1->RegisterYourself();
       TGeoConeSeg *Co1 = new TGeoConeSeg("Co1"+nm,dz+1.*cm,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,-1.,91.);

       TGeoTranslation *t2 = new TGeoTranslation("t2"+nm,-dxm+dcorner+thick,dym-dcorner-thick,0.);
       t2->RegisterYourself();
       TGeoConeSeg *Co2 = new TGeoConeSeg("Co2"+nm,dz+1.*cm,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,89.,181.);

       TGeoTranslation *t3 = new TGeoTranslation("t3"+nm,-dxm+dcorner+thick,-dym+dcorner+thick,0.);
       t3->RegisterYourself();
       TGeoConeSeg *Co3 = new TGeoConeSeg("Co3"+nm,dz+1.*cm,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,179.,271.);

       TGeoTranslation *t4 = new TGeoTranslation("t4"+nm,dxm-dcorner-thick,-dym+dcorner+thick,0.);
       t4->RegisterYourself();
       TGeoConeSeg *Co4 = new TGeoConeSeg("Co4"+nm,dz+1.*cm,dc1+thick,dc1+2.*m,dc2+thick,dc2+2.*m,269.,361.0);

       TGeoCompositeShape *T213 = new TGeoCompositeShape("T213"+nm,"T2"+nm+"-Co1"+nm+":t1"+nm+\
                                                         "-Co2"+nm+":t2"+nm+\
                                                         "-Co3"+nm+":t3"+nm+\
                                                         "-Co4"+nm+":t4"+nm);

       T = new TGeoVolume(xname, T213, material);
      }   
      T->SetLineColor(colour);
      //and make the volumes sensitive..
      if (sens) {AddSensitiveVolume(T);}
      return T;
}
// private method make support of vessel with rounded corners
TGeoVolume* veto::GeoVesselSupport(TString xname,Double_t thick,Double_t dz,Double_t dx_start,Double_t dy_start,Double_t slopeX,Double_t slopeY,Double_t dcorner,Int_t colour,TGeoMedium *material, Double_t floorHeight)
{

      TString nm = xname.ReplaceAll("-","");  //otherwise it will try to subtract "-" in TGeoComposteShape
      Double_t hhall=10.*m - floorHeight; //temporary vertical half-height of the hall
      Double_t dy1 = dy_start;
      Double_t dy2 = dy_start;
      if(slopeY>0){dy2 = dy1 + 2*slopeY*dz;}
      Double_t dx1 = dx_start;
      Double_t dx2 = dx1 ;
      if(slopeX>0){dx2 = dx1 + 2*slopeX*dz;}
      Double_t slopeSupport=0.2;
      Double_t dxl1=dx1+(hhall-dy1)*slopeSupport;
      Double_t dxl2=dx2+(hhall-dy2)*slopeSupport;
      Double_t exr=(dy2-dy1)/2.+(dx2-dx1)/2.;

      Double_t dc1=dcorner-exr/2.;
      Double_t dc2=dcorner+exr/2.;
      Double_t dxm=(dx1+dx2)/2.;
      Double_t dym=(dy1+dy2)/2.;
      
      TGeoArb8 *T2 = new TGeoArb8("T2"+nm,dz);
      Double_t tdx1 = dxm-exr/2.;
      Double_t tdx2 = dxm+exr/2.;
      Double_t tdy1 = dym-exr/2.;
      Double_t tdy2 = dym+exr/2.;

      T2->SetVertex(0,-dxl1,-hhall);
      T2->SetVertex(1,-tdx1,-tdy1+dcorner/2.);
      T2->SetVertex(2,tdx1,-tdy1+dcorner/2.);
      T2->SetVertex(3,dxl1,-hhall);
      T2->SetVertex(4,-dxl2,-hhall);
      T2->SetVertex(5,-tdx2,-tdy2+dcorner/2.);
      T2->SetVertex(6,tdx2,-tdy2+dcorner/2.);
      T2->SetVertex(7,dxl2,-hhall);

      TGeoVolume *T;
       //dcorner is the distance between the center of corner
       //circle and the inner edge of the object.
       tdx1 = dxm-exr/2.-dc1+0.1*cm;
       tdx2 = dxm+exr/2.-dc2+0.1*cm;
       tdy1 = dym-thick-exr/2.;
       tdy2 = dym-thick+exr/2.;

       TGeoArb8 *T3 = new TGeoArb8("T3"+nm,dz+2.E-6);
       T3->SetVertex(0,-tdx1,-tdy1);
       T3->SetVertex(1,-tdx1,tdy1);
       T3->SetVertex(2,tdx1,tdy1);
       T3->SetVertex(3,tdx1,-tdy1);
       T3->SetVertex(4,-tdx2,-tdy2);
       T3->SetVertex(5,-tdx2,tdy2);
       T3->SetVertex(6,tdx2,tdy2);
       T3->SetVertex(7,tdx2,-tdy2);

       //now subtract the corners using TGeoConeSeg
       TGeoConeSeg *Ci3 = new TGeoConeSeg("Ci3"+nm,dz+3.e-6,0.,dc1+thick,0.,dc2+thick,179.,271.);
       TGeoTranslation *t3 = new TGeoTranslation("t3"+nm,-dxm+dcorner+thick,-dym+dcorner+thick,0.);
       t3->RegisterYourself();

       TGeoConeSeg *Ci4 = new TGeoConeSeg("Ci4"+nm,dz+3.e-6,0.,dc1+thick,0.,dc2+thick,269.,361.);
       TGeoTranslation *t4 = new TGeoTranslation("t4"+nm,dxm-dcorner-thick,-dym+dcorner+thick,0.);
       t4->RegisterYourself();

       //try to make SHiP like logo in support
       //what is the "center of the support:
       Double_t ysc=-hhall+(-tdy1+hhall)/2.;
       Double_t swidth=30.*cm;
       TGeoTranslation *t5 = new TGeoTranslation("t5"+nm,0.,ysc,0.);
       t5->RegisterYourself();
       //6 cutouts...
       Double_t rc=(dxl1+dx1)/2.-swidth/2.;
       Double_t rc2=-dy2-ysc-swidth;
       Double_t rc5=rc=ysc+hhall-swidth;
       TGeoCompositeShape *T213 = new TGeoCompositeShape();
         
       if (swidth<rc && swidth<rc2 && swidth<rc5){
        Double_t alpha1=atan((ysc+hhall)/dx1)*180./TMath::Pi();
        Double_t alpha2=atan((ysc+hhall)/dxl1)*180./TMath::Pi();
        TGeoTubeSeg *SHiP1 = new TGeoTubeSeg("SHiP1"+nm,swidth,rc,dz+3.e-6,5.,alpha1-5.);
        TGeoTubeSeg *SHiP3 = new TGeoTubeSeg("SHiP3"+nm,swidth,rc,dz+3.e-6,180-alpha1+5.,175.);
        TGeoTubeSeg *SHiP4 = new TGeoTubeSeg("SHiP4"+nm,swidth,rc,dz+3.e-6,185.,180.+alpha2-5.);
        TGeoTubeSeg *SHiP6 = new TGeoTubeSeg("SHiP6"+nm,swidth,rc,dz+3.e-6,360.-alpha2+5.,355.);
        TGeoTubeSeg *SHiP2 = new TGeoTubeSeg("SHiP2"+nm,swidth,rc2,dz+3.e-6,alpha1+5.,180-alpha1-5.);
        rc=ysc+hhall-swidth;
        TGeoTubeSeg *SHiP5 = new TGeoTubeSeg("SHiP5"+nm,swidth,rc5,dz+3.e-6,180.+alpha2+5.,360.-alpha2-5.);
       
        T213 = new TGeoCompositeShape("T213"+nm,"T2"+nm+"-T3"+nm+\
                                                         "-Ci3"+nm+":t3"+nm+"-Ci4"+nm+":t4"+nm+\
                                                         "-SHiP1"+nm+":t5"+nm+"-SHiP2"+nm+":t5"+nm+\
                                                         "-SHiP3"+nm+":t5"+nm+"-SHiP4"+nm+":t5"+nm+\
                                                         "-SHiP5"+nm+":t5"+nm+"-SHiP6"+nm+":t5"+nm);
        }else{
        T213 = new TGeoCompositeShape("T213"+nm,"T2"+nm+"-T3"+nm+\
                                                         "-Ci3"+nm+":t3"+nm+"-Ci4"+nm+":t4"+nm);
        }
       T = new TGeoVolume(xname, T213, material);
       
      T->SetLineColor(colour);
      return T;
}


TGeoVolume* veto::MakeSegments(Int_t seg,Double_t dz,Double_t dx_start,Double_t dy_start,Double_t slopeX,Double_t slopeY,Double_t floorHeight)
{
      // dz is the half-length, dx1 half-width x at start, dx2 half-width at end
      TString nm;
      nm = "T"; nm += seg;
      TGeoVolumeAssembly *tTankVol = new TGeoVolumeAssembly(nm);
      //Assume ~1 m between ribs, calculate number of ribs
      Double_t dist =  0.8*m; //with Napoli design: 0.8 m 
      Int_t nribs = 2+dz*2./dist  ;
      Double_t ribspacing = (dz*2.-nribs*f_InnerSupportThickness)/(nribs-1)+f_InnerSupportThickness;

      //with rounded corners, cannot make "long" volumes, hence place all volmues
      // i.e. : inner wall, "vacuum", ribs, LiSc, out H-beam, and outter Al wall
      // in short sectors.
      //Another note: make H-profiles, hence add thickness of "f_InnerSupportThickness" twice!
      //              The inner wall is a comination of H-bar and conencting shield of same thickness
      //              Outer wall: is (Al) layer outside the H-bar covering everything.
      //some "new" variables
      Double_t hwidth=15.*cm; //half-width of a H-bar

      //Place vacuum in decay volume, need small steps segments in z too, otherwise
      //rounded corners approximation does not fit. 
      Double_t dcorner = 80.*cm; // radius of inner circle at corners of vessel.
      Double_t dx;
      dx = dx_start - f_OuterSupportThickness - f_VetoThickness - 2*f_InnerSupportThickness ;
      if (dcorner>0.95*dx) {dcorner=0.95*dx;}
      Double_t dy;
      nm+= "decayVol";
      TGeoVolumeAssembly *tDecayVol = new TGeoVolumeAssembly(nm);
      TGeoTranslation* Zero = new TGeoTranslation(0,0,0);
      for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc= -dz + (nr-0.5)*ribspacing;
        dx = dx_start - f_OuterSupportThickness - f_VetoThickness - 2*f_InnerSupportThickness  + slopeX*(nr-1)*ribspacing;
        dy = dy_start - f_OuterSupportThickness - f_VetoThickness - 2*f_InnerSupportThickness;
        if (slopeY>0) {dy+= slopeY*(nr-1)*ribspacing;}
        TString tmp = nm;
        tmp+="-";tmp+=nr;
        TGeoVolume* T = GeoTrapezoid(tmp,-1.,0.5*ribspacing-1.e-6,dx,dy,slopeX,slopeY,dcorner,1,decayVolumeMed);
        T->SetVisibility(kFALSE);
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc));
      }
      tTankVol->AddNode(tDecayVol,0, Zero);
      //now place inner wall
      dcorner+=f_InnerSupportThickness;
      nm = "T"; nm += seg;
      nm+= "Innerwall";
      TGeoVolumeAssembly *tInnerWall = new TGeoVolumeAssembly(nm);
      for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc= -dz + (nr-0.5)*ribspacing;
        dx = dx_start  - f_OuterSupportThickness - f_VetoThickness -f_InnerSupportThickness + slopeX*(nr-1)*ribspacing;
        dy = dy_start - f_OuterSupportThickness - f_VetoThickness-f_InnerSupportThickness;
        if (slopeY>0) {dy+= slopeY*(nr-1)*ribspacing;}
        TString tmp = nm;
        tmp+="-";tmp+=nr;
        TGeoVolume* T = GeoTrapezoid(tmp,f_InnerSupportThickness,0.5*ribspacing-1.e-6,dx,dy,slopeX,slopeY,dcorner,15,supportMedIn);
        tInnerWall->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc));
      }
      tTankVol->AddNode(tInnerWall,0, Zero);
      //now place ribs
      nm = "T"; nm += seg;
      nm+= "Rib";
      TGeoVolumeAssembly *tRib = new TGeoVolumeAssembly(nm);
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib = -dz +f_RibThickness/2. +nr*ribspacing;
        Double_t d = 1.;
        //T4 Here use ribs only 10 cm high, 1/3 of VetoThickness! Need it for the pressure...
        //if (seg==4){d = 1./3.;}
        dx = dx_start -(1.-d)*f_VetoThickness -f_OuterSupportThickness -f_InnerSupportThickness+slopeX*(zrib+dz-f_RibThickness);
        dy = dy_start -(1.-d)*f_VetoThickness -f_OuterSupportThickness-f_InnerSupportThickness;
        if (slopeY>0) {dy+=slopeY*(zrib+dz-f_RibThickness);}
        TString tmp = nm;
        tmp+="-";tmp+=nr;
        TGeoVolume* T = GeoTrapezoid(tmp,d*f_VetoThickness,f_RibThickness/2.,dx,dy,slopeX,slopeY,dcorner,15,ribMed);
        tRib->AddNode(T, nr, new TGeoTranslation(0, 0,zrib));
      }
      tTankVol->AddNode(tRib,0, Zero);
      //now place LiSc
      //if (seg!=4 && seg!=6){
      if (seg<3){
       Double_t zlength=(ribspacing -f_InnerSupportThickness)/2.;
       nm = "T"; nm += seg;
       nm+= "LiSc";
       TGeoVolumeAssembly *tLiSc = new TGeoVolumeAssembly(nm);
       for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc= -dz +f_RibThickness+zlength+(nr-1)*ribspacing;
        dx = dx_start -f_OuterSupportThickness -f_InnerSupportThickness + slopeX*(zlisc+dz-zlength);
        dy = dy_start -f_OuterSupportThickness-f_InnerSupportThickness;
        if (slopeY>0) {dy+= slopeY*(zlisc+dz-zlength);}
        TString tmp = nm;
        tmp+="-";tmp+=nr;
        TGeoVolume* T = GeoTrapezoid(tmp,f_VetoThickness,zlength,dx,dy,slopeX,slopeY,dcorner,kMagenta-10,vetoMed,kTRUE);
        tLiSc->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc));
       }
       tTankVol->AddNode(tLiSc,0, Zero);
       //now close LiSc volumes with Al plates
       dcorner+=f_InnerSupportThickness+f_VetoThickness;
       nm = "T"; nm += seg;
       nm+= "Outerwall";
       TGeoVolumeAssembly *tOuterwall = new TGeoVolumeAssembly(nm);
       for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc= -dz +f_RibThickness+zlength+(nr-1)*ribspacing;
        dx = dx_start + slopeX*(zlisc+dz-hwidth/2.);
        dy = dy_start ;
        if (slopeY>0) {dy+= slopeY*(zlisc+dz-hwidth/2.);}
        TString tmp = nm;
        tmp+="-";tmp+=nr;
        TGeoVolume* T = GeoTrapezoid(tmp,f_OuterSupportThickness,0.5*ribspacing-1.e-6-hwidth/2.,dx,dy,slopeX,slopeY,dcorner,18,supportMedOut);
        tOuterwall->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc));
       }
       tTankVol->AddNode(tOuterwall,0, Zero); 
      }else{
       dcorner+=f_InnerSupportThickness+f_VetoThickness;
      }
      dcorner+=f_OuterSupportThickness;
      //now place H-pieces of H-bars on the outside: make them 30.cm wide for the time being
      nm = "T"; nm += seg;
      nm+= "Hbar";
      TGeoVolumeAssembly *tHbar = new TGeoVolumeAssembly(nm);
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib = -dz +f_RibThickness/2. +nr*ribspacing;
        Double_t hw=hwidth;
        if (nr==0) {zrib=zrib+hwidth/2.; hw=hw/2.;}
        if (nr==nribs-1) {zrib=zrib-hwidth/2.; hw=hw/2.;}
        dx = dx_start -f_OuterSupportThickness+slopeX*(zrib+dz-hwidth);
        dy = dy_start -f_OuterSupportThickness;
        if (slopeY>0) {dy+=slopeY*(zrib+dz-hwidth);}
        TString tmp = nm;
        tmp+="-";tmp+=nr;
        TGeoVolume* T = GeoTrapezoid(tmp,f_InnerSupportThickness/2.,hw,dx,dy,slopeX,slopeY,dcorner,15,ribMed);
        tHbar->AddNode(T, nr, new TGeoTranslation(0, 0,zrib));
      }
      tTankVol->AddNode(tHbar,0, Zero); 
      //Thomas his "empty" volume around it all, but cannot fit, because of support bars
      //nm+= "decayVol";
      //TGeoVolume* S = GeoTrapezoid(nm,1.*cm,dz,dx_start+0.1,dy_start+0.1,slopeX,slopeY,dcorner,18,decayVolumeMed);
      //tDecayVol->AddNode(S, 1, new TGeoTranslation(0, 0, 0));
      //now place support to floor, but not in the magnet
      if (seg!=4){
      nm = "T"; nm += seg;
      nm+= "Vsup";
      TGeoVolumeAssembly *tVsup = new TGeoVolumeAssembly(nm);
      Int_t npp=3;
      if (nribs==3) {npp=2;}
      if (nribs==4) {npp=3;}
      for (Int_t nr=0; nr<nribs; nr+=npp) {
        Double_t zrib = -dz +f_RibThickness/2. +nr*ribspacing;
        dx = dx_start -f_OuterSupportThickness+slopeX*(zrib+dz-f_RibThickness);
        dy = dy_start -f_OuterSupportThickness;
        if (slopeY>0) {dy+=slopeY*(zrib+dz-f_RibThickness);}
        TString tmp = nm;
        tmp+="-";tmp+=nr;
        TGeoVolume* T = GeoVesselSupport(tmp,f_InnerSupportThickness,f_RibThickness/2.,dx,dy,slopeX,slopeY,dcorner,15,ribMed,floorHeight);
        tVsup->AddNode(T, nr, new TGeoTranslation(0, 0,zrib));
        //special support spacing for segment nr=1
        if (seg==1){
          if (nr==3) {npp=1;}
          if (nr==4) {npp=3;}
        }
      }
      tTankVol->AddNode(tVsup,0, Zero);         
      }

     return tTankVol;
}
TGeoVolume* veto::MakeLidSegments(Int_t seg,Double_t dx,Double_t dy)
{
      // dz is the half-length, dx1 half-width x at start, dx2 half-width at end
      TString nm;
      nm = "T"; nm += seg;
      nm+= "Lid";
      TGeoVolumeAssembly *tDecayVol = new TGeoVolumeAssembly(nm);
      //Assume ~1 m between ribs, calculate number of ribs
      Double_t dist =  0.8*m; //with Napoli design: 0.8 m 
      Int_t nribs = 2+dx*2./dist  ;
      Double_t ribspacing = (dx*2.-nribs*f_InnerSupportThickness)/(nribs-1)+f_InnerSupportThickness;

      Double_t hwidth=15.*cm; //half-width of a H-bar
      Double_t ribwidth=f_VetoThickness; //( but should become it owns indepent dimension )

      //place lid
      TGeoVolume *T1Lid = gGeoManager->MakeBox("T1Lidbox",supportMedIn,dx+f_InnerSupportThickness/2,dy,f_InnerSupportThickness/2.);
      T1Lid->SetLineColor(14);
      tDecayVol->AddNode(T1Lid, 1, new TGeoTranslation(0, 0, 0));

      //now place ribs
      nm = "T"; nm += seg;
      nm+= "LidRib";
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t xrib = -dx +f_RibThickness/2. +nr*ribspacing;
        TGeoVolume* T = gGeoManager->MakeBox(nm,supportMedIn,f_InnerSupportThickness/2.,dy,ribwidth/2.);
        T->SetLineColor(14);
        tDecayVol->AddNode(T, nr, new TGeoTranslation(xrib, 0,-ribwidth/2.-f_InnerSupportThickness/2.));
      }

      //add H-bars in the front
      nm = "T"; nm += seg;
      nm+= "LidH";
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t xrib = -dx +f_RibThickness/2. +nr*ribspacing;
        TGeoVolume* T = gGeoManager->MakeBox(nm,supportMedIn,hwidth,dy,f_InnerSupportThickness/2.);
        T->SetLineColor(14);
        tDecayVol->AddNode(T, nr, new TGeoTranslation(xrib, 0,-ribwidth-f_InnerSupportThickness));
      }
     return tDecayVol;
}
// private method create ellipsoids
TGeoVolume* veto::GeoEllipticalTube(const char* name,Double_t thick,Double_t a,Double_t b,Double_t dz,Int_t colour,TGeoMedium *material,Bool_t sens=kFALSE)
{
  /*make elliptical tube by subtraction
   tick is wall thickness
   a,b are inner ellipse radii, dz is the half-length
   will be put at z, with colour and material*/
       TGeoEltu *T2  = new TGeoEltu("T2",a+thick,b+thick,dz);
       TGeoEltu *T1  = new TGeoEltu("T1",a,b,dz+0.1);
       TGeoSubtraction *subtraction = new TGeoSubtraction(T2,T1);
       TGeoCompositeShape *Tc = new TGeoCompositeShape(name, subtraction);
       TGeoVolume *T = new TGeoVolume(name, Tc, material);

       T->SetLineColor(colour);
       //and make the volunes sensitive..
       if (sens) {AddSensitiveVolume(T);}
       return T;
}
// private method create plate with ellips hole in the center
void veto::GeoPlateEllipse(const char* name,Double_t thick,Double_t a,Double_t b,Double_t dz,Double_t z,Int_t colour,TGeoMedium *material,TGeoVolume *top)
{
  /*make plate with elliptical hole.
   plate has half width/height: a(b)+thick
   a,b are ellipse radii of hole, dz is the half-thickness of the plate
   will be put at z, with colour and material*/
       TGeoBBox *T2  = new TGeoBBox("T2", a+thick,b+thick,dz);
       TGeoEltu *T1  = new TGeoEltu("T1",a,b,dz+0.1);
       TGeoSubtraction *subtraction = new TGeoSubtraction(T2,T1);
       TGeoCompositeShape *Tc = new TGeoCompositeShape(name, subtraction);
       TGeoVolume *T = new TGeoVolume(name, Tc, material);

       T->SetLineColor(colour);
       top->AddNode(T, 1, new TGeoTranslation(0, 0, z));
}


// -----   Private method InitMedium 
Int_t veto::InitMedium(const char* name) 
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
// -------------------------------------------------------------------------
void veto::SetTubZpositions(Float_t z1, Float_t z2, Float_t z3, Float_t z4, Float_t z5, Float_t z6)
{
     fTub1z = z1;                                                 //!  z-position of tub1
     fTub2z = z2;                                                 //!  z-position of tub2
     fTub3z = z3;                                                 //!  z-position of tub3
     fTub4z = z4;                                                 //!  z-position of tub4
     fTub5z = z5;                                                 //!  z-position of tub5
     fTub6z = z6;                                                 //!  z-position of tub6
}

void veto::SetTublengths(Float_t l1, Float_t l2, Float_t l3, Float_t l4, Float_t l5, Float_t l6)
{
     fTub1length = l1;                                                 //!  half length of tub1
     fTub2length = l2;                                                 //!  half length of tub2
     fTub3length = l3;                                                 //!  half length of tub3
     fTub4length = l4;                                                 //!  half length of tub4
     fTub5length = l5;                                                 //!  half length of tub5
     fTub6length = l6;                                                 //!  half length of tub6
}

// -------------------------------------------------------------------------

Bool_t  veto::ProcessHits(FairVolume* vol)
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
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    fVolumeID = gGeoManager->FindVolumeFast(vol->GetName())->GetNumber();
    if (fELoss == 0. ) { return kFALSE; }
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos; 
    gMC->TrackPosition(Pos); 
    TLorentzVector Mom; 
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;      
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );

    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kVETO);
  }

  return kTRUE;
}

void veto::EndOfEvent()
{

  fvetoPointCollection->Clear();

}

void veto::PreTrack(){
    if (!fFastMuon){return;} 
    if (fabs(gMC->TrackPid())!=13){
        gMC->StopTrack(); 
    }
}
void veto::Register()
{

  /** This will create a branch in the output tree called
      vetoPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("vetoPoint", "veto",
                                        fvetoPointCollection, kTRUE);

}


TClonesArray* veto::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fvetoPointCollection; }
  else { return NULL; }
}

void veto::Reset()
{
  fvetoPointCollection->Clear();
}
void veto::SetZpositions(Float_t z0, Float_t z1, Float_t z2, Float_t z3, Float_t z4, Int_t c)
{
     fT0z = z0;            //!  z-position of veto station
     fT1z = z1;            //!  z-position of tracking station 1
     fT2z = z2;            //!  z-position of tracking station 2
     fT3z = z3;            //!  z-position of tracking station 3
     fT4z = z4;            //!  z-position of tracking station 4
     fDesign = c;  
}

void veto::ConstructGeometry()
{
 /*  decay tube, veto detectors and tracking detectors are closely related
     therefore, incorporate here the previously external defined ShipChamber
     and make the walls sensitive 
 */
    fLogger = FairLogger::GetLogger();
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("Concrete");
    TGeoMedium *concrete  =gGeoManager->GetMedium("Concrete");
    InitMedium("steel");
    TGeoMedium *St =gGeoManager->GetMedium("steel");
    InitMedium("vacuums");
    TGeoMedium *vac =gGeoManager->GetMedium("vacuums");
    InitMedium("Aluminum");
    TGeoMedium *Al =gGeoManager->GetMedium("Aluminum");
    InitMedium("ShipSens");
    TGeoMedium *Sens =gGeoManager->GetMedium("ShipSens");
    InitMedium("Scintillator");
    TGeoMedium *Se =gGeoManager->GetMedium("Scintillator");
    gGeoManager->SetNsegments(100);
    vetoMed        = gGeoManager->GetMedium(vetoMed_name);      //! medium of veto counter, liquid or plastic scintillator
    supportMedIn   = gGeoManager->GetMedium(supportMedIn_name); //! medium of support structure, iron, balloon
    supportMedOut  = gGeoManager->GetMedium(supportMedOut_name); //! medium of support structure, aluminium, balloon
    decayVolumeMed = gGeoManager->GetMedium(decayVolumeMed_name);  // decay volume, air/helium/vacuum
    ribMed = gGeoManager->GetMedium(ribMed_name); //! medium of support structure
    if (fDesign<4||fDesign>5){ fLogger->Fatal(MESSAGE_ORIGIN, "Only Designs 4 and 5 are supported!");}
    // put everything in an assembly
    TGeoVolume *tDecayVol = new TGeoVolumeAssembly("DecayVolume");
    TGeoVolume *tMaGVol   = new TGeoVolumeAssembly("MagVolume");
    Double_t zStartDecayVol = fTub1z-fTub1length-f_InnerSupportThickness;
    Double_t zStartMagVol = fTub3z+fTub3length-f_InnerSupportThickness; //? is this needed, -f_InnerSupportThickness
    if (fDesign==5){
    // designMakeSe 5: simplified trapezoidal design for optimization study
    // dz is the half-length, dx1 half-width x at start, dx2 half-width at end
      Double_t slopex = 2.83*m/(fTub6z - zFocusX);// size in TP design
      Double_t slopey = fBtube/(fTub6z - zFocusY); 
      Double_t zpos = fTub1z -fTub1length -f_InnerSupportThickness;
   // Add veto-timing sensitive plane before vacuum tube, same size as entrance window
      Double_t dx1 = slopex*(zpos - zFocusX);
      Double_t dy  = slopey*(zpos - zFocusY);
      TGeoVolume *VetoTimeDet = gGeoManager->MakeBox("VetoTimeDet",Sens,dx1,dy,10.*mm);
      VetoTimeDet->SetLineColor(kMagenta-10);
      top->AddNode(VetoTimeDet, 1, new TGeoTranslation(0, 0, fTub1z-fTub1length-45.*cm));
      AddSensitiveVolume(VetoTimeDet);
   // make the entrance window
      // add floor:
      Double_t floorHeight = 4.5 * m;
      Double_t Length = zStartMagVol - zStartDecayVol - 1.8*m; 
      TGeoBBox *box = new TGeoBBox("box1",  10 * m, floorHeight/2., Length/2.);
      TGeoVolume *floor = new TGeoVolume("floor1",box,concrete);
      floor->SetLineColor(11);
      tDecayVol->AddNode(floor, 0, new TGeoTranslation(0, -10*m+floorHeight/2.,Length/2.));
      //new lid made out of H-bars
      TGeoVolume* T1Lid = MakeLidSegments(1,dx1,dy);
      tDecayVol->AddNode(T1Lid, 1, new TGeoTranslation(0, 0, zpos - zStartDecayVol+f_InnerSupportThickness/2.1));
      TGeoVolume* seg1 = MakeSegments(1,fTub1length,dx1,dy,slopex,slopey,floorHeight);
      tDecayVol->AddNode(seg1, 1, new TGeoTranslation(0, 0, fTub1z - zStartDecayVol));
      dx1 = slopex*(fTub2z -fTub2length - zFocusX);
      dy  = slopey*(fTub2z -fTub2length - zFocusY);
      TGeoVolume* seg2 = MakeSegments(2,fTub2length,dx1,dy,slopex,slopey,floorHeight);
      tDecayVol->AddNode(seg2, 1, new TGeoTranslation(0, 0, fTub2z - zStartDecayVol));
      floorHeight = 2 * m;
      Length = fTub6z+fTub6length-fTub2z-fTub2length; 
      box = new TGeoBBox("box2",  10 * m, floorHeight/2., Length/2.);
      floor = new TGeoVolume("floor2",box,concrete);
      floor->SetLineColor(11);
      tMaGVol->AddNode(floor, 0, new TGeoTranslation(0, -10*m+floorHeight/2., Length/2.-2*fTub3length));
      dx1 = slopex*(fTub3z -fTub3length - zFocusX);
      dy = slopey*(fTub3z -fTub3length - zFocusY);
      TGeoVolume* seg3 = MakeSegments(3,fTub3length,dx1,dy,0.,0.,floorHeight);
      tMaGVol->AddNode(seg3, 1, new TGeoTranslation(0, 0, fTub3z - zStartMagVol));
      dx1 = slopex*(fTub4z -fTub4length - zFocusX);
      //dy = fBtube;
      dy = slopey*(fTub4z -fTub4length - zFocusY);
      TGeoVolume* seg4 = MakeSegments(4,fTub4length,dx1,dy,slopex,slopey,floorHeight);
      tMaGVol->AddNode(seg4, 1, new TGeoTranslation(0, 0, fTub4z - zStartMagVol));
      dx1 = slopex*(fTub5z -fTub5length - zFocusX);
      dy = slopey*(fTub5z -fTub5length - zFocusY);
      TGeoVolume* seg5 = MakeSegments(5,fTub5length,dx1,dy,0.,0.,floorHeight);
      tMaGVol->AddNode(seg5, 1, new TGeoTranslation(0, 0, fTub5z - zStartMagVol));
      dx1 = slopex*(fTub6z -fTub6length - zFocusX);
      dy = slopey*(fTub6z -fTub6length - zFocusY);
      Double_t dx2 = slopex*(fTub6z +fTub6length - zFocusX);
      TGeoVolume* seg6 = MakeSegments(6,fTub6length,dx1,dy,slopex,slopey,floorHeight);
      tMaGVol->AddNode(seg6, 1, new TGeoTranslation(0, 0, fTub6z - zStartMagVol));
   // make the exit window
      TGeoVolume *T6Lid = gGeoManager->MakeBox("T6Lid",supportMedIn,dx2,dy,f_InnerSupportThickness);
      T6Lid->SetLineColor(14);
      tMaGVol->AddNode(T6Lid, 1, new TGeoTranslation(0, 0,fTub6z+fTub6length+f_InnerSupportThickness - zStartMagVol));

      //finisMakeSeh assembly and position
      TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tDecayVol->GetShape());
      Double_t totLength = asmb->GetDZ();
      top->AddNode(tDecayVol, 1, new TGeoTranslation(0, 0,zStartDecayVol+totLength));
      asmb = dynamic_cast<TGeoShapeAssembly*>(tMaGVol->GetShape());
      totLength = asmb->GetDZ();
      top->AddNode(tMaGVol, 1, new TGeoTranslation(0, 0,zStartMagVol+totLength));

      //Add one more sensitive plane after vacuum tube for timing
      TGeoVolume *TimeDet = gGeoManager->MakeBox("TimeDet",Sens,dx2,fBtube,15.*mm);
      TimeDet->SetLineColor(kMagenta-10);
      top->AddNode(TimeDet, 1, new TGeoTranslation(0, 0, fTub6z+fTub6length+10.*cm));
      AddSensitiveVolume(TimeDet);
    }   
    else if (fDesign==4){
    // design 4: elliptical double walled tube with LiSci in between
    // Interpolate wall thicknesses based on the vertical size fBtube.
    // for Y=10m and vacuum: 
      Double_t walli=3.*cm; 
      Double_t wallo=8.*mm;
      // ignore variations with height
      //Double_t wallo=(2*fBtube-6.*m)*(8.-5.)*mm/(4.*m)+5.*mm;	
      //Double_t walli=(2*fBtube-6.*m)*(3.-2.)*cm/(4.*m)+2.*cm;	
      
      //Note: is just 2 cm for veto chamber, to avoid muon hits :-).
      Double_t atube    = 2.5*m;	
      Double_t btube    = fBtube;
      Double_t atube1   = 2.2*m-walli-wallo-f_VetoThickness;	
      
      //Entrance lid: first create Sphere
      Double_t lidradius = btube*2*1.3;
      TGeoSphere *lidT1I = new TGeoSphere("lidT1I",lidradius,lidradius+wallo,0.,90.,0.,360.);
      TGeoEltu *Ttmp1  = new TGeoEltu("Ttmp1",atube1+lidradius,btube+lidradius,lidradius+1.*m);
      TGeoEltu *Ttmp2  = new TGeoEltu("Ttmp2",atube1,btube,lidradius+1.*m);
      TGeoCompositeShape *LidT1 = new TGeoCompositeShape("LidT1", "lidT1I-(Ttmp1-Ttmp2)");
      TGeoVolume *T1Lid = new TGeoVolume("T1Lid", LidT1, Al );
      T1Lid->SetLineColor(14);
      tDecayVol->AddNode(T1Lid, 1, new TGeoTranslation(0, 0,fTub1z -fTub1length -lidradius+1.*m - zStartDecayVol));


      // All inner tubes...
      TGeoVolume *T = GeoEllipticalTube("T1I",walli,atube1,btube,fTub1length,18,St);
      tDecayVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub1z - zStartDecayVol));
      T = GeoEllipticalTube("T2I",walli,atube, btube,fTub2length,18,St);
      tDecayVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub2z - zStartDecayVol));
      T = GeoEllipticalTube("T3I",walli,atube, btube,fTub3length,18,St);
      tMaGVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub3z - zStartMagVol));
      T = GeoEllipticalTube("T4I",walli,atube, btube,fTub4length,18,St);
      tMaGVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub4z - zStartMagVol));
      T = GeoEllipticalTube("T5I",walli,atube, btube,fTub5length,18,St);
      tMaGVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub5z - zStartMagVol));
      T = GeoEllipticalTube("T6I",walli,atube, btube,fTub6length,18,St);
      tMaGVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub6z - zStartMagVol));
      // All outer tubes, first calculate inner radii of this tube
      Double_t aO =atube+walli+f_VetoThickness;
      Double_t aO1=atube1+walli+f_VetoThickness;
      Double_t bO =btube+walli+f_VetoThickness;
      T = GeoEllipticalTube("T1O",wallo,aO1,bO,fTub1length,14,Al);
      tDecayVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub1z - zStartDecayVol));
      T = GeoEllipticalTube("T2O",wallo,aO, bO,fTub2length,14,Al);
      tDecayVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub2z - zStartDecayVol));
      T = GeoEllipticalTube("T3O",wallo,aO, bO,fTub3length,14,Al);
      tDecayVol->AddNode(T, 1, new TGeoTranslation(0, 0, fTub3z - zStartDecayVol));
      T = GeoEllipticalTube("T5O",wallo,aO, bO,fTub5length,14,Al);
      tDecayVol->AddNode(T, 1, new TGeoTranslation(0, 0,fTub5z - zStartDecayVol));
      GeoPlateEllipse("T1Endplate",  0.02*m+(atube-atube1),aO1+wallo,bO+wallo,walli/2.,fTub1z+fTub1length-walli/2. - zStartDecayVol,18,St,tDecayVol);
      GeoPlateEllipse("T2Startplate",0.02*m+(atube-atube1),aO +wallo,bO+wallo,walli/2.,fTub2z-fTub2length+walli/2. - zStartDecayVol,18,St,tDecayVol);
      GeoPlateEllipse("T2Endplate"  ,ws                   ,aO +wallo,bO+wallo,walli/2.,fTub2z+fTub2length-walli/2. - zStartDecayVol,18,St,tDecayVol);
      GeoPlateEllipse("T3Startplate",ws                   ,aO +wallo,bO+wallo,walli/2.,fTub3z-fTub3length+walli/2. - zStartDecayVol,18,St,tDecayVol);
      GeoPlateEllipse("T3Endplate"  ,ws                   ,aO +wallo,bO+wallo,walli/2.,fTub3z+fTub3length-walli/2. - zStartMagVol,18,St,tMaGVol);
      GeoPlateEllipse("T4Startplate",ws                   ,aO +wallo,bO+wallo,walli/2.,fTub4z-fTub4length+walli/2. - zStartMagVol,18,St,tMaGVol);
      GeoPlateEllipse("T4Endplate"  ,ws                   ,aO +wallo,bO+wallo,walli/2.,fTub4z+fTub4length-walli/2. - zStartMagVol,18,St,tMaGVol);
      GeoPlateEllipse("T5Startplate",ws                   ,aO +wallo,bO+wallo,walli/2.,fTub5z-fTub5length+walli/2. - zStartMagVol,18,St,tMaGVol);
      GeoPlateEllipse("T5Endplate"  ,ws                   ,aO +wallo,bO+wallo,walli/2.,fTub5z+fTub5length-walli/2. - zStartMagVol,18,St,tMaGVol);
      GeoPlateEllipse("T6Startplate",ws                   ,aO +wallo,bO+wallo,walli/2.,fTub6z-fTub6length+walli/2. - zStartMagVol,18,St,tMaGVol);
      // And liquid scintillator inbetween, first calculate inner radii of this
      Double_t als =atube+walli;
      Double_t als1=atube1+walli;
      Double_t bls =btube+walli;

      //Assume ~1 m between ribs, calculate number of ribs
      Double_t dist = 1.*m; 
      //For Tube nr 1:
      Int_t nribs = 2+fTub1length*2./dist  ;
      Double_t ribspacing = (fTub1length*2.-nribs*walli)/(nribs-1)+walli;
      //now place ribs
      T = GeoEllipticalTube("T1Rib",f_VetoThickness,als1,bls,walli/2.,18,St);
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib= fTub1z-fTub1length+walli/2.+nr*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zrib - zStartDecayVol));
      }
      //now place LiSc
      Double_t zlength=(ribspacing-walli)/2.;
      T = GeoEllipticalTube("T1LiSc",f_VetoThickness,als1,bls,zlength,kMagenta-10,Se,true);
      for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc= fTub1z-fTub1length+walli+zlength+(nr-1)*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc - zStartDecayVol));
      }

      //For Tube nr 2:
      nribs = 2+fTub2length*2./dist  ;
      ribspacing = (fTub2length*2.-nribs*walli)/(nribs-1)+walli;
      zlength=(ribspacing-walli)/2.;
      T = GeoEllipticalTube("T2Rib",f_VetoThickness,als,bls,walli/2.,18,St);
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib= fTub2z-fTub2length+walli/2.+nr*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zrib - zStartDecayVol));
      }
      //now place LiSc
      T = GeoEllipticalTube("T2LiSc",f_VetoThickness,als,bls,zlength,kMagenta-10,Se,true);
      for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc=fTub2z-fTub2length+walli+zlength+(nr-1)*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc - zStartDecayVol));
      }

      //For Tube nr 3:
      nribs = 2+fTub3length*2./dist  ;
      ribspacing = (fTub3length*2.-nribs*walli)/(nribs-1)+walli;
      zlength=(ribspacing-walli)/2.;
      T = GeoEllipticalTube("T3Rib",f_VetoThickness,als,bls,walli/2.,18,St);
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib= fTub3z-fTub3length+walli/2.+nr*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zrib - zStartDecayVol));
      }
      //now place LiSc
      T = GeoEllipticalTube("T3LiSc",f_VetoThickness,als,bls,zlength,kMagenta-10,Se,true);
      for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc=fTub3z-fTub3length+walli+zlength+(nr-1)*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc - zStartDecayVol));
      }

      //For Tube nr 4:
      nribs = 2+fTub4length*2./dist  ;
      ribspacing = (fTub4length*2.-nribs*walli)/(nribs-1)+walli;
      zlength=(ribspacing-walli)/2.;
      //Here use ribs only 10 cm high!
      T = GeoEllipticalTube("T4Rib",f_VetoThickness/3.,als,bls,walli/2.,18,St);
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib= fTub4z-fTub4length+walli/2.+nr*ribspacing;
        tMaGVol->AddNode(T, nr, new TGeoTranslation(0, 0,zrib - zStartMagVol));
      }

      //For Tube nr 5:
      nribs = 2+fTub5length*2./dist  ;
      ribspacing = (fTub5length*2.-nribs*walli)/(nribs-1)+walli;
      zlength=(ribspacing-walli)/2.;
      T = GeoEllipticalTube("T5Rib",f_VetoThickness,als,bls,walli/2.,18,St);
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib= fTub5z-fTub5length+walli/2.+nr*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zrib - zStartDecayVol));
     }
      //now place LiSc
      T = GeoEllipticalTube("T5LiSc",f_VetoThickness,als,bls,zlength,kMagenta-10,Se,true);
      for (Int_t nr=1; nr<nribs; nr++) {
        Double_t zlisc=fTub5z-fTub5length+walli+zlength+(nr-1)*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zlisc - zStartDecayVol));
      }

      //For Tube nr 6:
      nribs = 2+fTub6length*2./dist  ;
      ribspacing = (fTub6length*2.-nribs*walli)/(nribs-1)+walli;
      zlength=(ribspacing-walli)/2.;
      T = GeoEllipticalTube("T6Rib",f_VetoThickness,als,bls,walli/2.,18,St);
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        Double_t zrib= fTub6z-fTub6length+walli/2.+nr*ribspacing;
        tDecayVol->AddNode(T, nr, new TGeoTranslation(0, 0,zrib - zStartDecayVol));
      }

      //Exit lid: first create Sphere
      TGeoSphere *lidT6I = new TGeoSphere("lidT6I",lidradius,lidradius+wallo,90.,180.,0.,360.);
      TGeoEltu *T6tmp1  = new TGeoEltu("T6tmp1",atube+lidradius,btube+lidradius,lidradius+1.*m);
      TGeoEltu *T6tmp2  = new TGeoEltu("T6tmp2",atube,btube,lidradius+1.*m);
      TGeoCompositeShape *LidT6 = new TGeoCompositeShape("LidT6", "lidT6I-(T6tmp1-T6tmp2)");
      TGeoVolume *T6Lid = new TGeoVolume("T6Lid", LidT6, Al );
      T6Lid->SetLineColor(14);
      tMaGVol->AddNode(T6Lid, 1, new TGeoTranslation(0, 0,fTub6z+fTub6length+lidradius-1.*m - zStartMagVol));
     
      //finish assembly and position
      TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tDecayVol->GetShape());
      Double_t totLength = asmb->GetDZ();
      top->AddNode(tDecayVol, 1, new TGeoTranslation(0, 0,zStartDecayVol+totLength));
      asmb = dynamic_cast<TGeoShapeAssembly*>(tMaGVol->GetShape());
      totLength = asmb->GetDZ();
      top->AddNode(tMaGVol, 1, new TGeoTranslation(0, 0,zStartMagVol+totLength));

      //Add one more sensitive plane after vacuum tube for timing
      TGeoVolume *TimeDet = gGeoManager->MakeBox("TimeDet",Sens,3.*m,6.*m,15.*mm);
      TimeDet->SetLineColor(kMagenta-10);
      top->AddNode(TimeDet, 1, new TGeoTranslation(0, 0, fTub6z+fTub6length+10.*cm));
      AddSensitiveVolume(TimeDet);

      //Add veto-timing sensitive plane before vacuum tube 
      TGeoVolume *VetoTimeDet = gGeoManager->MakeBox("VetoTimeDet",Sens,aO1+wallo/2.,6.*m,10.*mm);
      VetoTimeDet->SetLineColor(kMagenta-10);
      top->AddNode(VetoTimeDet, 1, new TGeoTranslation(0, 0, fTub1z-fTub1length-5.*cm));
      AddSensitiveVolume(VetoTimeDet);

//Add one sensitive plane counting rate in second detector downstream
      // with shielding around, 
      TGeoVolume *tDet2 = new TGeoVolumeAssembly("Detector2");
      Double_t zStartDet2 = fTub6z + 50.*m;
      Double_t thickness = 10.*cm /2.;
      TGeoBBox *shield2Out = new TGeoBBox("shield2Out",2.5*m+thickness, 3*m+thickness, 20.*cm+thickness);
      TGeoBBox *shield2In  = new TGeoBBox("shield2In", 2.5*m+0.1*cm, 3*m+0.1*cm, 20.*cm+0.1*cm);
      TGeoCompositeShape *shieldDet2 = new TGeoCompositeShape("shieldDet2", "shield2Out-shield2In");
      TGeoVolume *sdet2 = new TGeoVolume("shieldDet2", shieldDet2, St);
      sdet2->SetLineColor(kWhite-5);
      tDet2->AddNode(sdet2, 1, new TGeoTranslation(0, 0, 0));
      TGeoVolume *Det2 = gGeoManager->MakeBox("Det2", Sens, 2.5*m, 3.*m, 5.*cm);
      Det2->SetLineColor(kGreen+3);
      tDet2->AddNode(Det2, 1, new TGeoTranslation(0, 0, 0));       
      AddSensitiveVolume(Det2);
      asmb = dynamic_cast<TGeoShapeAssembly*>(tDet2->GetShape());
      totLength = asmb->GetDZ();
      top->AddNode(tDet2, 1, new TGeoTranslation(0, 0,zStartDet2+totLength));
     }

// only for fastMuon simulation, otherwise output becomes too big    
     if (fFastMuon){
        const char* Vol  = "TGeoVolume";
        const char* Mag  = "Mag";
        const char* Rock = "rock";
        const char* Ain  = "AbsorberAdd";
        const char* Aout = "AbsorberAddCore";
        TObjArray* volumelist = gGeoManager->GetListOfVolumes();
        int lastvolume = volumelist->GetLast();
        int volumeiterator=0;
        while ( volumeiterator<=lastvolume ) {
         const char* volumename = volumelist->At(volumeiterator)->GetName();
         const char* classname  = volumelist->At(volumeiterator)->ClassName();
         if (strstr(classname,Vol)){
          if (strstr(volumename,Mag) || strstr(volumename,Rock)|| strstr(volumename,Ain) || strstr(volumename,Aout)){ 
            AddSensitiveVolume(gGeoManager->GetVolume(volumename));
            cout << "veto added "<< volumename <<endl;
          }
         }  
         volumeiterator++;
        }
     }

}

vetoPoint* veto::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fvetoPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "veto hit called "<< pos.z()<<endl;
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode,Lpos,Lmom);
}

ClassImp(veto)
