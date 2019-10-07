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
#include "TMath.h"


#include <iostream>
#include <vector>
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
  fUseSupport=1;
  fPlasticVeto=0;
  fLiquidVeto=1;
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
    fFollowMuon(kFALSE),
    fT0z(-2390.),              //!  z-position of veto station
    fT1z(1510.),               //!  z-position of tracking station 1
    fT2z(1710.),               //!  z-position of tracking station 2
    fT3z(2150.),               //!  z-position of tracking station 3
    fT4z(2370.),               //!  z-position of tracking station 4
    f_InnerSupportThickness(3.*cm),    //!  inner support thickness of decay volume
    f_OuterSupportThickness(8.*mm),    //!  outer support thickness of decay volume
    f_LidThickness(80.*mm),    //!  thickness of Al entrance and exit lids
    f_PhiRibsThickness(15.*mm),    //!  thickness ribs for phi segmentation
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
    ribMed_name("steel"),             //material of the ribs(support structure)
    phi_ribMed_name("polypropylene"),//material of the phi_ribs (structure separating  the LiSc segments in XY plane)
    f_RibThickness(3.*cm),
    decayVolumeMed_name("vacuums")    // for vacuum option
{
  fUseSupport=1;
  fPlasticVeto=0;
  fLiquidVeto=1;
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


TGeoVolume* veto::GeoTrapezoidNew(TString xname,Double_t thick,Double_t wz,
				  Double_t wX_start,Double_t wX_end,
				  Double_t wY_start,Double_t wY_end,
				  Int_t color,TGeoMedium *material,Bool_t sens=kFALSE)
{
      
      
      
      Double_t dx_start=wX_start/2;
      Double_t dy_start=wY_start/2;
      Double_t dx_end=wX_end/2;
      Double_t dy_end=wY_end/2;
      Double_t dz=wz/2;
      
  
      TString nm = xname.ReplaceAll("-","");  //otherwise it will try to subtract "-" in TGeoComposteShape
      Double_t dx1 = dx_start+thick;
      Double_t dx2 = dx_end+thick;
      Double_t dy1 = dy_start+thick;
      Double_t dy2 = dy_end+thick;

      TGeoArb8 *T2 = new TGeoArb8("T2"+nm,dz);
      T2->SetVertex(0,-dx1,-dy1); T2->SetVertex(1,-dx1,dy1); T2->SetVertex(2,dx1,dy1); T2->SetVertex(3,dx1,-dy1);
      T2->SetVertex(4,-dx2,-dy2); T2->SetVertex(5,-dx2,dy2); T2->SetVertex(6,dx2,dy2); T2->SetVertex(7,dx2,-dy2);

       Double_t tdx1 = dx_start;
       Double_t tdx2 = dx_end;
       Double_t tdy1 = dy_start;
       Double_t tdy2 = dy_end;
       TGeoArb8 *T1 = new TGeoArb8("T1"+nm,dz+1.E-6);
       T1->SetVertex(0,-tdx1,-tdy1); T1->SetVertex(1,-tdx1,tdy1); T1->SetVertex(2,tdx1,tdy1); T1->SetVertex(3,tdx1,-tdy1);
       T1->SetVertex(4,-tdx2,-tdy2); T1->SetVertex(5,-tdx2,tdy2); T1->SetVertex(6,tdx2,tdy2); T1->SetVertex(7,tdx2,-tdy2);

       
       TGeoCompositeShape *T321 = new TGeoCompositeShape("T3"+nm,"T2"+nm+"-T1"+nm);
       TGeoVolume *T = new TGeoVolume(xname, T321, material);
	T->SetLineColor(color);
      //and make the volunes sensitive..
      if (sens) {AddSensitiveVolume(T);}
      return T;
}




double wx(double z){
  
  double wx1=1520*mm;
  double wx2=2522*mm;
  double z1=0*m;
  double z2=14.4*m;
  if(z>14.4*m){
    z1=14.4*m;
    z2=15.2*m;
    wx1=2522*mm;
    wx2=2578*mm;
    if(z>15.2*m){
      z1=15.2*m;
      z2=24.0*m;
      wx1=2578*mm;
      wx2=3190*mm;
      if(z>24.0*m){
	z1=24.0*m;
	z2=33.6*m;
	wx1=3190*mm;
	wx2=3859*mm;
	if(z>33.6*m){
	  z1=33.6*m;
	  z2=50.0*m;
	  wx1=3859*mm;
	  wx2=5000*mm;
	}
      }
    }
  }
  
  return wx1+(z-z1)*(wx2-wx1)/(z2-z1);
}

double wy(double z){
  
  double wy1=4320*mm;
  double wy2=6244*mm;
  double z1=0*m;
  double z2=14.4*m;
  if(z>14.4*m){
    z1=14.4*m;
    z2=15.2*m;
    wy1=6244*mm;
    wy2=6350*mm;
    if(z>15.2*m){
      z1=15.2*m;
      z2=24.0*m;
      wy1=6350*mm;
      wy2=7526*mm;
      if(z>24.0*m){
	z1=24.0*m;
	z2=33.6*m;
	wy1=7526*mm;
	wy2=8809*mm;
	if(z>33.6*m){
	  z1=33.6*m;
	  z2=50.0*m;
	  wy1=8809*mm;
	  wy2=11000*mm;
	}
      }
    }
  }
  
  return wy1+(z-z1)*(wy2-wy1)/(z2-z1);
}


TGeoVolume* veto::GeoSideObj(TString xname, double dz,
			     double a1, double b1,double a2, double b2,double dA, double dB,
				Int_t color, TGeoMedium *material, Bool_t sens=kFALSE){

  //a1- width in X, at the beginning
  //b1- width in Y, at the beginning
  //a2- width in X, at the end
  //b2- width in Y, at the end
  
      TGeoArb8 *T1 = new TGeoArb8(dz);
      T1->SetVertex(0,0,0);
      T1->SetVertex(1,0,b1);  
      T1->SetVertex(2,a1,b1);    
      T1->SetVertex(3,a1,0);   
      
      T1->SetVertex(4,dA,dB);
      T1->SetVertex(5,dA,dB+b2);
      T1->SetVertex(6,dA+a2,dB+b2);
      T1->SetVertex(7,dA+a2,dB);

  
  
      TGeoVolume *T = new TGeoVolume(xname, T1, material);
      T->SetLineColor(color);
      //and make the volunes sensitive..
      if (sens) {AddSensitiveVolume(T);}
      return T;
}


TGeoVolume* veto::GeoCornerLiSc1(TString xname, double dz,bool isClockwise,
			     double a, double b1,double b2, double dA, double dB,
				Int_t color, TGeoMedium *material, Bool_t sens=kFALSE){

      TGeoArb8 *T1 = new TGeoArb8(dz);
      
      if(isClockwise){
	T1->SetVertex(0,0,0);
	T1->SetVertex(1,0,b1);  
	T1->SetVertex(2,a+b1,b1);    
	T1->SetVertex(3,a,0);   

	T1->SetVertex(4,dA,dB);
	T1->SetVertex(5,dA,dB+b2);
	T1->SetVertex(6,dA+a+b2,dB+b2);
	T1->SetVertex(7,dA+a,dB);
      }
      else{
	T1->SetVertex(0,0,0);
	T1->SetVertex(1,-a,0);   
	T1->SetVertex(2,-a-b1,b1);    
	T1->SetVertex(3,0,b1);  

	T1->SetVertex(4,-dA,dB);
	T1->SetVertex(5,-dA-a,dB);
	T1->SetVertex(6,-dA-a-b2,dB+b2);
	T1->SetVertex(7,-dA,dB+b2);
      }
  
  
      TGeoVolume *T = new TGeoVolume(xname, T1, material);
      T->SetLineColor(color);
      //and make the volunes sensitive..
      if (sens) {AddSensitiveVolume(T);}
      return T;
}

TGeoVolume* veto::GeoCornerLiSc2(TString xname, double dz,bool isClockwise,
			     double a, double b1,double b2, double dA, double dB,
				Int_t color, TGeoMedium *material, Bool_t sens=kFALSE){

      TGeoArb8 *T1 = new TGeoArb8(dz);
      
      if(isClockwise){
	T1->SetVertex(0,0,0);
	T1->SetVertex(1,0,a);  
	T1->SetVertex(2,b1,a+b1);    
	T1->SetVertex(3,b1,0);   

	T1->SetVertex(4,dA,dB);
	T1->SetVertex(5,dA,dB+a);
	T1->SetVertex(6,dA+b2,dB+a+b2);
	T1->SetVertex(7,dA+b2,dB);
      }
      else{
	T1->SetVertex(0,0,0);
	T1->SetVertex(1,b1,0);   
	T1->SetVertex(2,b1,-a-b1);    
	T1->SetVertex(3,0,-a);  

	T1->SetVertex(4,dA,-dB);
	T1->SetVertex(5,dA+b2,-dB);
	T1->SetVertex(6,dA+b2,-dB-a-b2);
	T1->SetVertex(7,dA,-dB-a);
      }
  
  
      TGeoVolume *T = new TGeoVolume(xname, T1, material);
      T->SetLineColor(color);
      //and make the volunes sensitive..
      if (sens) {AddSensitiveVolume(T);}
      return T;
}


TGeoVolumeAssembly* veto::GeoCornerRib(TString xname, double ribThick, double lt1,double lt2, double dz, double slopeX, double slopeY, 
				Int_t color, TGeoMedium *material, Bool_t sens=kFALSE){
  
    Double_t wz=dz*2;
    double d=ribThick*sqrt(2)/2;
    double dx=slopeX*wz;
    double dy=slopeY*wz;
    
      TGeoArb8 *T1 = new TGeoArb8(dz);
      T1->SetVertex(0,lt1,lt1-d);
      T1->SetVertex(1,0,-d);   
      T1->SetVertex(2,0,0);    
      T1->SetVertex(3,lt1,lt1);  
      
      T1->SetVertex(4,dx+lt2,dy+lt2-d);
      T1->SetVertex(5,dx,dy-d);
      T1->SetVertex(6,dx,dy);
      T1->SetVertex(7,dx+lt2,dy+lt2);
      
      TGeoArb8 *T2 = new TGeoArb8(dz);
      T2->SetVertex(0,lt1-d,lt1);
      T2->SetVertex(1,lt1,lt1);   
      T2->SetVertex(2,0,0);    
      T2->SetVertex(3,-d,0);  
      
      T2->SetVertex(4,dx+lt2-d,dy+lt2);
      T2->SetVertex(5,dx+lt2,dy+lt2);
      T2->SetVertex(6,dx,dy);
      T2->SetVertex(7,dx-d,dy);
      
      
      
     TGeoVolume *T1v = new TGeoVolume("part", T1, material);
     TGeoVolume *T2v = new TGeoVolume("part", T2, material);
      T1v->SetLineColor(color);
      T2v->SetLineColor(color);
      if (sens) {AddSensitiveVolume(T1v);}
      if (sens) {AddSensitiveVolume(T2v);}
      
      
      
      TGeoVolumeAssembly *T = new TGeoVolumeAssembly(xname);
      T->AddNode(T1v,1, new TGeoTranslation(0, 0,0));
      T->AddNode(T2v,2, new TGeoTranslation(0, 0,0));
      return T;
}
    
    
int veto::makeId(double z,double x, double y){
  double Z=z/10;
  double r=sqrt(x*x+y*y);
  double phi=999;
  if(y>=0)phi=acos(x/r);
  else phi=-acos(x/r)+2*TMath::Pi();
  
  phi=phi*180/TMath::Pi();
  return (int)Z*1000000 + (int)r*1000 + (int)phi;
}        


void veto::AddBlock(TGeoVolumeAssembly *tInnerWall,TGeoVolumeAssembly *tOuterWall,TGeoVolumeAssembly *tLongitRib,TGeoVolumeAssembly *tVerticalRib,TGeoVolumeAssembly *ttLiSc, int& liScCounter,
                     TString blockName , int nx, int ny,
		    double z1, double z2 , double Zshift, double dist, double distC,
		    double wallThick, double liscThick1, double liscThick2,double ribThick  ){
  
  
            int ribColor=15;
  
	      double wz=(z2-z1);
	      double slX=(wx(z2)-wx(z1))/2/wz;
	      double slY=(wy(z2)-wy(z1))/2/wz;
	      
	      double dZ = (dist-ribThick)/2; //half space between ribs
	      
	      	    
	      double tX=0;
	      double tY=0;
	      double tZ=0;
	      TString name("");
	      
	      double idX=0;
	      double idY=0;
	      double idZ=0;
	      
	      
	      //inner wall
	      TString nameInnerWall = (TString)tInnerWall->GetName()+"_"+blockName; 
	      TGeoVolume* TIW = GeoTrapezoidNew(nameInnerWall,wallThick,wz,wx(z1),wx(z2),wy(z1),wy(z2),ribColor,supportMedIn);
	      tInnerWall->AddNode(TIW,0, new TGeoTranslation(0, 0,Zshift ));
	      
	      //outer wall
	      TString nameOuterWall = (TString)tOuterWall->GetName()+"_"+blockName; 
	      TGeoVolume* TOW = GeoTrapezoidNew(nameOuterWall,wallThick,wz,
						   wx(z1)+2*(wallThick+liscThick1),wx(z2)+2*(wallThick+liscThick2),wy(z1)+2*(wallThick+liscThick1),wy(z2)+2*(wallThick+liscThick2),ribColor,supportMedIn);
	      tOuterWall->AddNode(TOW, 0 , new TGeoTranslation(0, 0,Zshift));
	      

	      //vertical ribs, longitudinal, and lisc:
	      //corner ribs
	      name="CornerRib_L_"+blockName+"_id";
	      TGeoVolumeAssembly* CornerRib_L_b1 = GeoCornerRib(name,ribThick, liscThick1,liscThick2,dZ, slX,slY, ribColor ,supportMedIn);
	      name="CornerRib_R_"+blockName+"_id";
	      TGeoVolumeAssembly* CornerRib_R_b1 = GeoCornerRib(name,ribThick, liscThick1,liscThick2,dZ, slY,slX, ribColor ,supportMedIn);
	      
	      std::vector<TGeoVolume*> vLongitRibX_b1(nx);
	      std::vector<TGeoVolume*> vLongitRibY_b1(ny);
	      double xStep1=(wx(z1+ribThick)+2*wallThick-2*distC)/(nx-1);//rib thiknes + lisc size
	      double xStep2=(wx(z1+dist)+2*wallThick-2*distC)/(nx-1);
	      double yStep1=(wy(z1+ribThick)+2*wallThick-2*distC)/(ny-1);
	      double yStep2=(wy(z1+dist)+2*wallThick-2*distC)/(ny-1);
	      for(int i=0;i<nx;i++){
		double xpos1=wx(z1+ribThick)/2+wallThick-distC-ribThick/2-i*xStep1;
		double xpos2=wx(z1+dist)/2+wallThick-distC-ribThick/2-i*xStep2;
		double ypos1=wy(z1+ribThick)/2+wallThick;
		double ypos2=wy(z1+dist)/2+wallThick;
		name=""; name.Form("vLongitRibX_%s_phi%d",blockName.Data(),makeId(0,xpos1,ypos1));
		vLongitRibX_b1.at(i) = GeoSideObj(name, dZ,ribThick, liscThick1,ribThick, liscThick2,xpos2-xpos1, ypos2-ypos1,ribColor, supportMedIn);
	      }
	      for(int i=0;i<ny;i++){
		double xpos1=wx(z1+ribThick)/2+wallThick;
		double xpos2=wx(z1+dist)/2+wallThick;
		double ypos1=wy(z1+ribThick)/2+wallThick-distC-ribThick/2-i*yStep1;
		double ypos2=wy(z1+dist)/2+wallThick-distC-ribThick/2-i*yStep2;
		name=""; name.Form("vLongitRibX_%s_phi%d",blockName.Data(),makeId(0,xpos1,ypos1));
		vLongitRibY_b1.at(i) = GeoSideObj(name, dZ, liscThick1,ribThick, liscThick2,ribThick, xpos2-xpos1, ypos2-ypos1,ribColor, supportMedIn);
	      }
	      
	      //corners lisc
	      double xPos1=wx(z1+ribThick)/2+wallThick-distC+ribThick/2;
	      double xPos2=wx(z1+dist)/2+wallThick-distC+ribThick/2;
	      double yPos1=wy(z1+ribThick)/2+wallThick;
	      double yPos2=wy(z1+dist)/2+wallThick;
	      TGeoVolume* CornerLiSc_L1_b1 = GeoCornerLiSc1("CornerLiSc_L1_"+blockName,dZ,1,distC-ribThick/sqrt(2)-ribThick/2, liscThick1,liscThick2, xPos2-xPos1, yPos2-yPos1, kMagenta-10 ,vetoMed,true);
	      TGeoVolume* CornerLiSc_R1_b1 = GeoCornerLiSc1("CornerLiSc_R1_"+blockName,dZ,0,distC-ribThick/sqrt(2)-ribThick/2, liscThick1,liscThick2, xPos2-xPos1, yPos2-yPos1, kMagenta-10 ,vetoMed,true);
	      xPos1=wx(z1+ribThick)/2+wallThick;
	      xPos2=wx(z1+dist)/2+wallThick;
	      yPos1=wy(z1+ribThick)/2+wallThick-distC+ribThick/2;	
	      yPos2=wy(z1+dist)/2+wallThick-distC+ribThick/2;
	      TGeoVolume* CornerLiSc_L2_b1 = GeoCornerLiSc2("CornerLiSc_L2_"+blockName,dZ,1,distC-ribThick/sqrt(2)-ribThick/2, liscThick1,liscThick2, xPos2-xPos1, yPos2-yPos1, kMagenta-10 ,vetoMed,true);
	      TGeoVolume* CornerLiSc_R2_b1 = GeoCornerLiSc2("CornerLiSc_R2_"+blockName,dZ,0,distC-ribThick/sqrt(2)-ribThick/2, liscThick1,liscThick2, xPos2-xPos1, yPos2-yPos1, kMagenta-10 ,vetoMed,true);
	      
	      for(double pos=z1;pos<z2;pos+=dist){
                  //place vertical ribs 		
		  TString nameVR(""); nameVR.Form("VetoVerticalRib_z%d",(int)pos);
		  TGeoVolume* TVR = GeoTrapezoidNew(nameVR,liscThick1,
						       ribThick,wx(pos)+2*wallThick,wx(pos+ribThick)+2*wallThick,wy(pos)+2*wallThick,wy(pos+ribThick)+2*wallThick,ribColor,supportMedIn);
		  tZ=Zshift-wz/2+pos-z1+ribThick/2;
	          tVerticalRib->AddNode(TVR,0, new TGeoTranslation(0, 0,tZ ));
		  if(z2-pos<dist)continue;
	      
		  //place longitudinal ribs in the corners
		  tX=wx(pos+ribThick)/2+wallThick; 
	          tY=wy(pos+ribThick)/2+wallThick ;
		  tZ=tZ+ribThick/2+(dist-ribThick)/2;
		  tLongitRib->AddNode(CornerRib_L_b1, makeId(pos,tX,tY) , new TGeoCombiTrans(tX,tY,tZ,new TGeoRotation("r",0,0,0)));
		  tLongitRib->AddNode(CornerRib_L_b1, makeId(pos,-tX,-tY) , new TGeoCombiTrans(-tX,-tY,tZ,new TGeoRotation("r",0,0,180)));
		  tLongitRib->AddNode(CornerRib_R_b1, makeId(pos,-tX,tY) , new TGeoCombiTrans(-tX,tY,tZ,new TGeoRotation("r",0,0,90)));
		  tLongitRib->AddNode(CornerRib_R_b1, makeId(pos,tX,-tY) , new TGeoCombiTrans(tX,-tY,tZ,new TGeoRotation("r",0,0,270)));
		  
		  //place longitudinal ribs and lisc on the sides
		  
		  idZ = pos+ribThick/2+dist/2;
		  
		    //x side
		      double xStepZ1=(wx(pos+ribThick)+2*wallThick-2*distC)/(nx-1);
		      double xStepZ2=(wx(pos+dist)+2*wallThick-2*distC)/(nx-1);
		      for(int i=0;i<nx;i++){
			  
			  double xpos1=wx(pos+ribThick)/2+wallThick-distC-ribThick/2-i*xStepZ1;
			  double ypos1=wy(pos+ribThick)/2+wallThick;
			  tLongitRib->AddNode(vLongitRibX_b1.at(i), makeId(pos,xpos1,ypos1) , new TGeoCombiTrans(xpos1,ypos1,tZ,new TGeoRotation("r",0,0,0)));
			  tLongitRib->AddNode(vLongitRibX_b1.at(i), makeId(pos,-xpos1,-ypos1) , new TGeoCombiTrans(-xpos1,-ypos1,tZ,new TGeoRotation("r",0,0,180)));
			  //lisc
			    if(i<nx-1){
			      double xpos2=wx(pos+dist)/2+wallThick-distC-ribThick/2-i*xStepZ2;
			      double ypos2=wy(pos+dist)/2+wallThick;
			      name=""; name.Form("LiScX_%s_id%d", blockName.Data() ,makeId(idZ,xpos1-xStepZ1+ribThick,ypos1));
			      TGeoVolume* LiScX_b1 = GeoSideObj(name, dZ,xStepZ1-ribThick, liscThick1,xStepZ2-ribThick, liscThick2,
							 (xpos2-xStepZ2)-(xpos1-xStepZ1), ypos2-ypos1,kMagenta-10,vetoMed,true);
			      
			      idX = ((TGeoBBox*)LiScX_b1->GetShape())->GetOrigin()[0] + xpos1-xStepZ1+ribThick;
                  idY = ((TGeoBBox*)LiScX_b1->GetShape())->GetOrigin()[1] + ypos1;
                  ttLiSc->AddNode(LiScX_b1, liScCounter++ , new TGeoCombiTrans(xpos1-xStepZ1+ribThick,ypos1,tZ,new TGeoRotation("r",0,0,0))); 
                  ttLiSc->AddNode(LiScX_b1, liScCounter++ , new TGeoCombiTrans(-(xpos1-xStepZ1+ribThick),-ypos1,tZ,new TGeoRotation("r",0,0,180)));
			  }
		      }
		      
		     
		    //y side
		      double yStepZ1=(wy(pos+ribThick)+2*wallThick-2*distC)/(ny-1);
		      double yStepZ2=(wy(pos+dist)+2*wallThick-2*distC)/(ny-1);
		      for(int i=0;i<ny;i++){
			  double xpos1=wx(pos+ribThick)/2+wallThick;
			  double ypos1=wy(pos+ribThick)/2+wallThick-distC-ribThick/2-i*yStepZ1;
			  tLongitRib->AddNode(vLongitRibY_b1.at(i), makeId(pos,xpos1,ypos1) , new TGeoCombiTrans(xpos1,ypos1,tZ,new TGeoRotation("r",0,0,0)));
			  tLongitRib->AddNode(vLongitRibY_b1.at(i), makeId(pos,-xpos1,-ypos1) , new TGeoCombiTrans(-xpos1,-ypos1,tZ,new TGeoRotation("r",0,0,180)));
			 //lisc 
			  if(i<ny-1){
			      double xpos2=wx(pos+dist)/2+wallThick;
			      double ypos2=wy(pos+dist)/2+wallThick-distC-ribThick/2-i*yStepZ2;
			      name=""; name.Form("LiScY_%s_id%d",blockName.Data(),makeId(idZ,xpos1,ypos1-yStepZ1+ribThick));
			      TGeoVolume* LiScY_b1 = GeoSideObj(name, dZ,liscThick1, yStepZ1-ribThick, liscThick2, yStepZ2-ribThick, 
							 xpos2-xpos1, (ypos2-yStepZ2)-(ypos1-yStepZ1), kMagenta-10,vetoMed,true);
			      
			      idX = ((TGeoBBox*)LiScY_b1->GetShape())->GetOrigin()[0] + xpos1;
		              idY = ((TGeoBBox*)LiScY_b1->GetShape())->GetOrigin()[1] + ypos1-yStepZ1+ribThick;
                  ttLiSc->AddNode(LiScY_b1, liScCounter++ , new TGeoCombiTrans(  xpos1,  ypos1-yStepZ1+ribThick,tZ,new TGeoRotation("r",0,0,0)));
                  ttLiSc->AddNode(LiScY_b1, liScCounter++ , new TGeoCombiTrans(-xpos1,-(ypos1-yStepZ1+ribThick),tZ,new TGeoRotation("r",0,0,180)));
			  }
			  
		      }
		      
		      
		  //place lisc in the corners
		    double xP1=wx(pos+ribThick)/2+wallThick-distC+ribThick/2;
		    double yP1=wy(pos+ribThick)/2+wallThick;
		    idX = ((TGeoBBox*)CornerLiSc_L1_b1->GetShape())->GetOrigin()[0] + xP1;
		    idY = ((TGeoBBox*)CornerLiSc_L1_b1->GetShape())->GetOrigin()[1] + yP1;
            ttLiSc->AddNode(CornerLiSc_L1_b1, liScCounter++ , new TGeoCombiTrans(xP1,yP1,tZ,new TGeoRotation("r",0,0,0)));
            ttLiSc->AddNode(CornerLiSc_L1_b1, liScCounter++ , new TGeoCombiTrans(-xP1,-yP1,tZ,new TGeoRotation("r",0,0,180)));
		    
		    idX = ((TGeoBBox*)CornerLiSc_R1_b1->GetShape())->GetOrigin()[0] - xP1;
		    idY = ((TGeoBBox*)CornerLiSc_R1_b1->GetShape())->GetOrigin()[1] + yP1;
            ttLiSc->AddNode(CornerLiSc_R1_b1, liScCounter++ , new TGeoCombiTrans(-xP1,yP1,tZ,new TGeoRotation("r",0,0,0)));
		    ttLiSc->AddNode(CornerLiSc_R1_b1, liScCounter++ , new TGeoCombiTrans(xP1,-yP1,tZ,new TGeoRotation("r",0,0,180)));
            
		    xP1=wx(pos+ribThick)/2+wallThick;
		    yP1=wy(pos+ribThick)/2+wallThick-distC+ribThick/2;
		    idX = ((TGeoBBox*)CornerLiSc_L2_b1->GetShape())->GetOrigin()[0] + xP1;
		    idY = ((TGeoBBox*)CornerLiSc_L2_b1->GetShape())->GetOrigin()[1] + yP1;
            ttLiSc->AddNode(CornerLiSc_L2_b1, liScCounter++ , new TGeoCombiTrans(xP1,yP1,tZ,new TGeoRotation("r",0,0,0)));
		    ttLiSc->AddNode(CornerLiSc_L2_b1, liScCounter++ , new TGeoCombiTrans(-xP1,-yP1,tZ,new TGeoRotation("r",0,0,180)));
		    idX = ((TGeoBBox*)CornerLiSc_R2_b1->GetShape())->GetOrigin()[0] + xP1;
		    idY = ((TGeoBBox*)CornerLiSc_R2_b1->GetShape())->GetOrigin()[1] - yP1;
            ttLiSc->AddNode(CornerLiSc_R2_b1, liScCounter++ , new TGeoCombiTrans(xP1,-yP1,tZ,new TGeoRotation("r",0,0,0)));
            ttLiSc->AddNode(CornerLiSc_R2_b1, liScCounter++ , new TGeoCombiTrans(-xP1,yP1,tZ,new TGeoRotation("r",0,0,180)));
	      }
	    
	      
}


TGeoVolume* veto::MakeMagnetSegment(Int_t seg){
      TString nm;
      nm = "T"; nm += seg;
      TGeoVolumeAssembly *tMagVol = new TGeoVolumeAssembly(nm);
      
      bool isVert = 1;
      bool isLongOutCover = 1;
      
       double dzMagnetPart = 238.1*cm ; //from Piets Wertelaers drawings 
       double thiknes = 12*mm;    
       double xPos=0;
       double yPos=0;
       double zPos=0;
       
      //make walls inside magnet area
        double dx=5*cm;//from Piets Wertelaers drawings 
        double dy=500*cm;//from Piets Wertelaers drawings 
        double dz=dzMagnetPart;
        TGeoVolume*  InnerMagWall_Y =  gGeoManager->MakeBox("InnerMagWall_Y", supportMedIn, dx, dy, dz);
	InnerMagWall_Y->SetLineColor(15);
	tMagVol->AddNode(InnerMagWall_Y, 1 , new TGeoCombiTrans(255*cm,0,0,new TGeoRotation("r",0,0,0)));
	tMagVol->AddNode(InnerMagWall_Y, 2 , new TGeoCombiTrans(-255*cm,0,0,new TGeoRotation("r",0,0,0)));
	
	dx=260*cm;//from Piets Wertelaers drawings 
        dy=5*cm;//from Piets Wertelaers drawings 
        dz=dzMagnetPart;
        TGeoVolume*  InnerMagWall_X =  gGeoManager->MakeBox("InnerMagWall_X", supportMedIn, dx, dy, dz);
	InnerMagWall_X->SetLineColor(15);
	tMagVol->AddNode(InnerMagWall_X, 1 , new TGeoCombiTrans(0,505*cm,0,new TGeoRotation("r",0,0,0)));
	tMagVol->AddNode(InnerMagWall_X, 2 , new TGeoCombiTrans(0,-505*cm,0,new TGeoRotation("r",0,0,0)));
	
	
	
	xPos=(-358.2*cm-250.4*cm)/2;
	yPos=602.4*cm-(602.4-500.4)*cm/2;
	zPos=dzMagnetPart+thiknes/2;
	
	dx=(358.2-250.4)*cm/2;
	dy=604.4*cm;
	dz=thiknes/2;
	TGeoVolume*  VertMagCover_Y =  gGeoManager->MakeBox("VertMagCover_Y", supportMedIn, dx, dy, dz);
	dx=250.4*cm;
	dy=(602.4-500.4)*cm/2;
	TGeoVolume*  VertMagCover_X =  gGeoManager->MakeBox("VertMagCover_X", supportMedIn, dx, dy, dz);
	VertMagCover_Y->SetLineColor(15);
	VertMagCover_X->SetLineColor(15);
	
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 1 , new TGeoCombiTrans(xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 2 , new TGeoCombiTrans(-xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 3 , new TGeoCombiTrans(xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 4 , new TGeoCombiTrans(-xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
	
	if(isVert)tMagVol->AddNode(VertMagCover_X, 1 , new TGeoCombiTrans(0,yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 2 , new TGeoCombiTrans(0,-yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 3 , new TGeoCombiTrans(0,yPos,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 4 , new TGeoCombiTrans(0,-yPos,-zPos,new TGeoRotation("r",0,0,0)));
	
    
    double dxOoutCover=thiknes/2;
    double dyOoutCover=604.4*cm; 
    double dzOoutCover=56.0*cm/2;
    double xPosOutetCover = xPos-(358.2-250.4)*cm/2;
    double yPosOutetCover = 602.4*cm;
    double zPosOutetCover = zPos-dzOoutCover-thiknes/2;
    
    TGeoVolume*  LongOutCover_Y1 =  gGeoManager->MakeBox("LongOutCover_Y1", supportMedIn, dxOoutCover, dyOoutCover, dzOoutCover);
    dxOoutCover=fabs(xPosOutetCover)-thiknes;
    dyOoutCover=thiknes/2;
    TGeoVolume*  LongOutCover_X1 =  gGeoManager->MakeBox("LongOutCover_X1", supportMedIn, dxOoutCover, dyOoutCover, dzOoutCover);
    
    LongOutCover_Y1->SetLineColor(15);
    LongOutCover_X1->SetLineColor(15);
    
	if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y1, 1 , new TGeoCombiTrans(xPosOutetCover,0,zPosOutetCover,new TGeoRotation("r",0,0,0)));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y1, 2 , new TGeoCombiTrans(-xPosOutetCover,0,zPosOutetCover,new TGeoRotation("r",0,0,0)));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y1, 3 , new TGeoCombiTrans(xPosOutetCover,0,-zPosOutetCover,new TGeoRotation("r",0,0,0)));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y1, 4 , new TGeoCombiTrans(-xPosOutetCover,0,-zPosOutetCover,new TGeoRotation("r",0,0,0)));
     
     
	if(isLongOutCover)tMagVol->AddNode(LongOutCover_X1, 1 , new TGeoCombiTrans(0,yPosOutetCover,zPosOutetCover,new TGeoRotation("r",0,0,0)));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_X1, 2 , new TGeoCombiTrans(0,-yPosOutetCover,zPosOutetCover,new TGeoRotation("r",0,0,0)));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_X1, 3 , new TGeoCombiTrans(0,yPosOutetCover,-zPosOutetCover,new TGeoRotation("r",0,0,0)));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_X1, 4 , new TGeoCombiTrans(0,-yPosOutetCover,-zPosOutetCover,new TGeoRotation("r",0,0,0)));
    
    
    zPos=328.5*cm;
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 5 , new TGeoCombiTrans(xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 6 , new TGeoCombiTrans(-xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 7 , new TGeoCombiTrans(xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 8 , new TGeoCombiTrans(-xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
    
    if(isVert)tMagVol->AddNode(VertMagCover_X, 5 , new TGeoCombiTrans(0,yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 6 , new TGeoCombiTrans(0,-yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 7 , new TGeoCombiTrans(0,yPos,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 8 , new TGeoCombiTrans(0,-yPos,-zPos,new TGeoRotation("r",0,0,0)));
    
	zPos=442.3*cm;
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 9 , new TGeoCombiTrans(xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 10 , new TGeoCombiTrans(-xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 11 , new TGeoCombiTrans(xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 12 , new TGeoCombiTrans(-xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
    
    if(isVert)tMagVol->AddNode(VertMagCover_X, 9 , new TGeoCombiTrans(0,yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 10 , new TGeoCombiTrans(0,-yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 11 , new TGeoCombiTrans(0,yPos,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 12 , new TGeoCombiTrans(0,-yPos,-zPos,new TGeoRotation("r",0,0,0)));
    
    
	zPos=532.1*cm;
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 10 , new TGeoCombiTrans(xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 11 , new TGeoCombiTrans(-xPos,0,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 12 , new TGeoCombiTrans(xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_Y, 13 , new TGeoCombiTrans(-xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
    
    if(isVert)tMagVol->AddNode(VertMagCover_X, 10 , new TGeoCombiTrans(0,yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 11 , new TGeoCombiTrans(0,-yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 12 , new TGeoCombiTrans(0,yPos,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 13 , new TGeoCombiTrans(0,-yPos,-zPos,new TGeoRotation("r",0,0,0)));
    
    zPos=589.3*cm;
	if(isVert)tMagVol->AddNode(VertMagCover_X, 14 , new TGeoCombiTrans(0,yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 15 , new TGeoCombiTrans(0,-yPos,zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 16 , new TGeoCombiTrans(0,yPos,-zPos,new TGeoRotation("r",0,0,0)));
	if(isVert)tMagVol->AddNode(VertMagCover_X, 17 , new TGeoCombiTrans(0,-yPos,-zPos,new TGeoRotation("r",0,0,0)));
    
    dx=(358.2-250.4)*cm/2-37.0*cm/2;
	dy=604.4*cm;
	dz=thiknes/2;
    xPos+=37.0*cm/2;
	TGeoVolume*  VertMagCover_y =  gGeoManager->MakeBox("VertMagCover_y", supportMedIn, dx, dy, dz);
    VertMagCover_y->SetLineColor(15);
    if(isVert)tMagVol->AddNode(VertMagCover_y, 1 , new TGeoCombiTrans(xPos,0,zPos,new TGeoRotation("r",0,0,0)));
    if(isVert)tMagVol->AddNode(VertMagCover_y, 2 , new TGeoCombiTrans(-xPos,0,zPos,new TGeoRotation("r",0,0,0)));
    if(isVert)tMagVol->AddNode(VertMagCover_y, 3 , new TGeoCombiTrans(xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
    if(isVert)tMagVol->AddNode(VertMagCover_y, 4 , new TGeoCombiTrans(-xPos,0,-zPos,new TGeoRotation("r",0,0,0)));
    
    
    dx=thiknes/2;
    dy=604.4*cm; 
    dz=88.5*cm/2;
    TGeoVolume*  LongOutCover_Y2 =  gGeoManager->MakeBox("LongOutCover_Y2", supportMedIn, dx, dy, dz);
    LongOutCover_Y2->SetLineColor(15);

    xPos = xPosOutetCover;
    yPos = 0*cm;
    zPos = 283.65*cm;
    
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 1 , new TGeoTranslation(xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 2 , new TGeoTranslation(xPos,yPos,-zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 3 , new TGeoTranslation(-xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 4 , new TGeoTranslation(-xPos,yPos,-zPos));

    xPos=-323.0*cm;
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 5 , new TGeoTranslation(xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 6 , new TGeoTranslation(xPos,yPos,-zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 7 , new TGeoTranslation(-xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 8 , new TGeoTranslation(-xPos,yPos,-zPos));
    
    xPos = xPosOutetCover;
    zPos = 487.2*cm;
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 9 , new TGeoTranslation(xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 10 , new TGeoTranslation(xPos,yPos,-zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 11 , new TGeoTranslation(-xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 12 , new TGeoTranslation(-xPos,yPos,-zPos));

    xPos=-323.0*cm;
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 13 , new TGeoTranslation(xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 14 , new TGeoTranslation(xPos,yPos,-zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 16 , new TGeoTranslation(-xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y2, 17 , new TGeoTranslation(-xPos,yPos,-zPos));
    
    
    dz=112.6*cm/2;
    TGeoVolume*  LongOutCover_Y3 =  gGeoManager->MakeBox("LongOutCover_Y3", supportMedIn, dx, dy, dz);
    LongOutCover_Y3->SetLineColor(15);
    xPos = xPosOutetCover;
    zPos = 385.4*cm;
    
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y3, 1 , new TGeoTranslation(xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y3, 2 , new TGeoTranslation(xPos,yPos,-zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y3, 3 , new TGeoTranslation(-xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y3, 4 , new TGeoTranslation(-xPos,yPos,-zPos));
    
    
    dy-=(358.2-250.4)*cm;
    TGeoVolume*  LongOutCover_Y4 =  gGeoManager->MakeBox("LongOutCover_Y4", supportMedIn, dx, dy, dz);
    LongOutCover_Y4->SetLineColor(2);
    
    xPos=-255.0*cm;
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y4, 1 , new TGeoTranslation(xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y4, 2 , new TGeoTranslation(xPos,yPos,-zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y4, 3 , new TGeoTranslation(-xPos,yPos,zPos));
    if(isLongOutCover)tMagVol->AddNode(LongOutCover_Y4, 4 , new TGeoTranslation(-xPos,yPos,-zPos));
    
    
    /*
    dxOoutCover=fabs(xPosOutetCover)-thiknes;
    dyOoutCover=thiknes/2;
    TGeoVolume*  LongOutCover_X2 =  gGeoManager->MakeBox("LongOutCover_X1", supportMedIn, dxOoutCover, dyOoutCover, dzOoutCover);
    
    LongOutCover_X2->SetLineColor(15);
    */
	
	 
      return tMagVol;
  
  
}


TGeoVolume* veto::MakeSegments(Double_t dz,Double_t dx_start,Double_t dy_start,Double_t slopeX,Double_t slopeY,Double_t floorHeight)
{
      TGeoVolumeAssembly *tTankVol = new TGeoVolumeAssembly("T2");
      Double_t dist =  0.8*m; //with Napoli design: 0.8 m
      

      //>>>>>>>>>>>>>>>>>>>>>>>>>>>>new>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

	  int isOuterWall=0;
	  int isInnerWall=1;
	  int isVerticalRib=1;
	  int isLongitRib=1;
	  int isLiSc=1;
	  
	  
	  //assembly for innerwall
	    TString nameInnerWall = "VetoInnerWall";  
	    TGeoVolumeAssembly *tInnerWall = new TGeoVolumeAssembly(nameInnerWall);
	  //assembly for outerwall
	    TString nameOuterWall = "VetoOuterWall";  
	    TGeoVolumeAssembly *tOuterWall = new TGeoVolumeAssembly(nameOuterWall);
	  //assembly for longitudinal rib
	    TString nameLongitRib = "VetoLongitRib";  
	    TGeoVolumeAssembly *tLongitRib = new TGeoVolumeAssembly(nameLongitRib);
	  //assembly for vertical ribs
	    TString nameVerticalRib = "VetoVerticalRib";  
	    TGeoVolumeAssembly *tVerticalRib = new TGeoVolumeAssembly(nameVerticalRib);
	  //assembly for liqued scintilator
	    TString nameLiSc = "VetoLiSc";  
	    TGeoVolumeAssembly *ttLiSc = new TGeoVolumeAssembly(nameLiSc);
        int liScCounter=0;

	  //********************************   Block1: ************************************************************* 
	    double z1=0*m;
	    double z2=14.4*m;
	    double wz=(z2-z1);//to delete
	    double slX=(wx(z2)-wx(z1))/2/wz;//to delete
	    double slY=(wy(z2)-wy(z1))/2/wz;//to delete
	    
	    double wallThick= 20*mm;//wall thiknes
	    double liscThick1= 300*mm;
	    double liscThick2= 300*mm;
	    double ribThick = 10*mm;
	    
	    double Zshift=-dz + wz/2;//calibration of Z position
	    double shiftPlot=0;//calibration of Z position
	    
	    int nx=4; // number of Longitudinal ribs on X
	    int ny=6; // number of Longitudinal ribs on Y
	    
	    double distC = 150*mm; //rib distance from corner
 

	    
	   AddBlock(tInnerWall,tOuterWall,tLongitRib,tVerticalRib,ttLiSc, liScCounter,
                    "block1", nx, ny, z1,z2,Zshift,dist,distC,
                wallThick,liscThick1,liscThick2,ribThick);
	      
	      

	      
	      
// 	  //********************************   Block2 part1:   ************************************************************* 
	    Zshift+=wz/2;
	    z1=14.4*m;
	    z2=15.2*m;
	    wz=(z2-z1);
	    Zshift+=wz/2;
	    liscThick2=410*mm;
// 	    
// 	    Zshift+=shiftPlot;
// 	    
	    AddBlock(tInnerWall,tOuterWall,tLongitRib,tVerticalRib,ttLiSc, liScCounter,
                     "block2p1", nx, ny, z1,z2,Zshift,dist,distC,
		      wallThick,liscThick1,liscThick2,ribThick);

	  //********************************   Block2 part2:    ************************************************************* 
	    Zshift+=wz/2;
	    z1=15.2*m;
	    z2=24.0*m;
	    wz=z2-z1;
	    Zshift+=wz/2;
// 	    
// 	    Zshift+=shiftPlot;
// 	    
	    liscThick1=410*mm;
	    	   AddBlock(tInnerWall,tOuterWall,tLongitRib,tVerticalRib,ttLiSc, liScCounter,
                    "block2p2", nx, ny, z1,z2,Zshift,dist,distC,
		     wallThick,liscThick1,liscThick2,ribThick);
   
// 
// 	  //********************************   Block2 part3:    ************************************************************* 
	    Zshift+=wz/2;
	    z1=24.0*m;
	    z2=33.6*m;
	    wz=z2-z1;
	    Zshift+=wz/2;

// 	    Zshift+=shiftPlot;
// 	    
	     nx=7;//number of Longitudinal ribs on X
	    ny=11;//number of Longitudinal ribs on Y
	    
	  	   AddBlock(tInnerWall,tOuterWall,tLongitRib,tVerticalRib,ttLiSc, liScCounter,
                    "block2p3", nx, ny, z1,z2,Zshift,dist,distC,
		     wallThick,liscThick1,liscThick2,ribThick);

//   
	  //********************************   Block3:    ************************************************************* 
	    Zshift+=wz/2;
	    z1=33.6*m;
	    z2=50.0*m;
	    wz=z2-z1;
	    Zshift+=wz/2;
	    
	    wallThick= 30*mm;
	    liscThick1=390*mm;
	    liscThick2=390*mm;
	    
// 	    Zshift+=shiftPlot;
// 	    
           	   AddBlock(tInnerWall,tOuterWall,tLongitRib,tVerticalRib,ttLiSc, liScCounter,
                    "block3", nx, ny, z1,z2,Zshift,dist,distC,
		     wallThick,liscThick1,liscThick2,ribThick);
	      
	      

	 if(isInnerWall)tTankVol->AddNode(tInnerWall,0, new TGeoTranslation(0, 0,0 ));
	 if(isOuterWall)tTankVol->AddNode(tOuterWall,0, new TGeoTranslation(0, 0,0 ));
	 if(isVerticalRib)tTankVol->AddNode(tVerticalRib,0, new TGeoTranslation(0, 0,0 ));
	 if(isLongitRib)tTankVol->AddNode(tLongitRib,0, new TGeoTranslation(0, 0,0 ));
	 if(isLiSc)tTankVol->AddNode(ttLiSc,0, new TGeoTranslation(0, 0,0 ));

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
      //TGeoVolume *T1Lid = gGeoManager->MakeBox("T1Lidbox",supportMedIn,dx+f_InnerSupportThickness/2,dy,f_InnerSupportThickness/2.);
      //make it out of 8 mm of Al.
      TGeoVolume *T1Lid = gGeoManager->MakeBox("T1Lidbox",supportMedOut,dx+f_InnerSupportThickness/2,dy,f_LidThickness/2.);
      T1Lid->SetLineColor(18);
      tDecayVol->AddNode(T1Lid, 1, new TGeoTranslation(0, 0, 0));


      //Do not place H-bar ribs anymore..
      if (1==0){
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
      }
     return tDecayVol;
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
    if (fELoss == 0. ) { return kFALSE; }

    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();

    Int_t veto_uniqueId;
    gMC->CurrentVolID(veto_uniqueId);
    if (veto_uniqueId>1000000) //Solid scintillator case
    {
      Int_t vcpy;
      gMC->CurrentVolOffID(1, vcpy);
      if (vcpy==5) veto_uniqueId+=4; //Copy of half
    }

    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;
//    cout << veto_uniqueId << " :(" << xmean << ", " << ymean << ", " << zmean << "): " << gMC->CurrentVolName() << endl;
    AddHit(fTrackID, veto_uniqueId, TVector3(xmean, ymean,  zmean),
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
    if (TMath::Abs(gMC->TrackPid())!=13){
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
          floorHeightA=floorHeightA*0.5;
 
    fLogger = FairLogger::GetLogger();
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("Concrete");
    TGeoMedium *concrete  =gGeoManager->GetMedium("Concrete");
    InitMedium("steel");
    TGeoMedium *polypropylene = gGeoManager->GetMedium("polypropylene");
    InitMedium("polypropylene");
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
    phi_ribMed=gGeoManager->GetMedium(phi_ribMed_name); //medium of the  structure separating  the LiSc segments in XY plane
    // put everything in an assembly
    TGeoVolume *tDecayVol = new TGeoVolumeAssembly("DecayVolume");
    TGeoVolume *tMaGVol   = new TGeoVolumeAssembly("MagVolume");
    Double_t zStartDecayVol = fTub1z-fTub1length-f_InnerSupportThickness;
    Double_t zStartMagVol = fTub3z+fTub3length-f_InnerSupportThickness; //? is this needed, -f_InnerSupportThickness
    
      Double_t d = f_VetoThickness+2*f_RibThickness+f_OuterSupportThickness;
      Double_t slopex = (2.5*m + d)/(fTub6z-fTub6length - zFocusX);
      Double_t slopey = (fBtube + d) /(fTub6z-fTub6length - zFocusY);
      Double_t zpos = fTub1z -fTub1length -f_LidThickness;
      Double_t dx1 = slopex*(zpos - zFocusX);
      Double_t dy  = slopey*(zpos - zFocusY);
   // make the entrance window
      // add floor:
      Double_t Length = zStartMagVol - zStartDecayVol - 2.2*m;
      TGeoBBox *box = new TGeoBBox("box1",  10 * m, floorHeightA/2., Length/2.);
      TGeoVolume *floor = new TGeoVolume("floor1",box,concrete);
      floor->SetLineColor(11);
      tDecayVol->AddNode(floor, 0, new TGeoTranslation(0, -10*m+floorHeightA/2.,Length/2.));
      //entrance lid
      TGeoVolume* T1Lid = MakeLidSegments(1,dx1,dy);
      tDecayVol->AddNode(T1Lid, 1, new TGeoTranslation(0, 0, zpos - zStartDecayVol+f_LidThickness/2.1));

      //without segment1, recalculate the z and (half)length of segment 2:
      //Take into account to remove the between seg1 and seg2 due to straw-veto station.
      //and add this gap to the total length.
      Double_t tgap=fTub2z-fTub1z-fTub2length-fTub1length;
      fTub2z=fTub1z+fTub2length+tgap/2.;
      fTub2length=fTub2length+fTub1length+tgap/2.;
      TGeoVolume* seg2 = MakeSegments(fTub2length,dx1,dy,slopex,slopey,floorHeightA);
      tDecayVol->AddNode(seg2, 1, new TGeoTranslation(0, 0, fTub2z-zStartDecayVol));
//////////////?????
      Length = fTub6length+fTub2length+3*m; // extend under ecal and muon detectors
      box = new TGeoBBox("box2",  10 * m, floorHeightB/2., Length/2.);
      floor = new TGeoVolume("floor2",box,concrete);
      floor->SetLineColor(11);
      tMaGVol->AddNode(floor, 0, new TGeoTranslation(0, -10*m+floorHeightB/2., Length/2.-2*fTub3length - 0.5*m));

      TGeoVolume*  magnetInnerWalls = MakeMagnetSegment(3);
      tMaGVol->AddNode(magnetInnerWalls, 1, new TGeoTranslation(0, 0, fTub4z - zStartMagVol));
      //tDecayVol->AddNode(magnetInnerWalls, 1, new TGeoTranslation(0, 0, fTub4z - zStartMagVol));
      
      
      
   // make the exit window
      Double_t dx2 = slopex*(fTub6z +fTub6length - zFocusX);
      TGeoVolume *T6Lid = gGeoManager->MakeBox("T6Lid",supportMedOut,dx2,dy,f_LidThickness/2.);
      T6Lid->SetLineColor(18);
      T6Lid->SetLineColor(2);
      T6Lid->SetFillColor(2);
      tMaGVol->AddNode(T6Lid, 1, new TGeoTranslation(0, 0,fTub6z+fTub6length+f_LidThickness/2.+0.1*cm - zStartMagVol));
      //finisMakeSegments assembly and position
      top->AddNode(tDecayVol, 1, new TGeoTranslation(0, 0,zStartDecayVol));
      top->AddNode(tMaGVol, 1, new TGeoTranslation(0, 0,zStartMagVol));


// only for fastMuon simulation, otherwise output becomes too big
     if (fFastMuon && fFollowMuon){
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

void veto::InnerAddToMap(Int_t ncpy, Double_t x, Double_t y, Double_t z, Double_t dx, Double_t dy, Double_t dz)
{
  if (fCenters.find(ncpy)!=fCenters.end())
  {
    cout << ncpy << " is already in the map" << endl;
    return;
  }
  fCenters[ncpy]=TVector3(x, y, z);
}

ClassImp(veto)
