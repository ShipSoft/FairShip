#include "ShipMagnet.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
//#include "FairGeoMedia.h"
//#include "FairGeoBuilder.h"

#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoElement.h"
#include "TGeoEltu.h"
#include "TGeoMedium.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc



ShipMagnet::~ShipMagnet()
{
}
ShipMagnet::ShipMagnet()
  : FairModule("ShipMagnet", "")
{
}

ShipMagnet::ShipMagnet(const char* name, const char* Title, Double_t z, Int_t c, Double_t dx, Double_t dy, Double_t fl, Double_t YW, Double_t YD, Double_t CT)
  : FairModule(name ,Title)
{
 fDesign = c;
 fSpecMagz = z; 
 fDy = dy;
 fDx = dx;
 floorheight = fl;
 YokeWidth = YW;
 YokeDepth = YD;
 CoilThick = CT;
}
 
// -----   Private method InitMedium 
Int_t ShipMagnet::InitMedium(const char* name) 
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
// private method make support of magnet
TGeoVolume* ShipMagnet::MagnetSupport(Double_t hwidth,Double_t hheight,Double_t dz,Int_t colour,TGeoMedium *material)
{

      TGeoBBox *ms = new TGeoBBox("ms", hwidth,hheight-1.,dz);
      //try to make SHiP like logo in support
      Double_t swidth=30.; //
       //6 cutouts from the front
       Double_t r25=hheight-swidth/2.;
       Double_t r1346=hwidth-swidth/2;
       Double_t alpha=atan(hheight/hwidth)*180./TMath::Pi();
       TGeoTubeSeg *FL1 = new TGeoTubeSeg("FL1",swidth,r1346,dz+1.,5.,alpha-5.);
       TGeoTubeSeg *FL3 = new TGeoTubeSeg("FL3",swidth,r1346,dz+1.,180-alpha+5.,175.);
       TGeoTubeSeg *FL4 = new TGeoTubeSeg("FL4",swidth,r1346,dz+1.,185.,180.+alpha-5.);
       TGeoTubeSeg *FL6 = new TGeoTubeSeg("FL6",swidth,r1346,dz+1.,360.-alpha+5.,355.);
       TGeoTubeSeg *FL2 = new TGeoTubeSeg("FL2",swidth,r25,dz+1.,alpha+5.,180-alpha-5.);
       TGeoTubeSeg *FL5 = new TGeoTubeSeg("FL5",swidth,r25,dz+1.,180.+alpha+5.,360.-alpha-5.);

       //6 cutouts from the side
       r1346=dz-swidth/2;
       alpha=atan(hheight/dz)*180./TMath::Pi();
       //cout << "magsupport: "<< swidth<<", "<<r25<<", "<< r1346<<", "<<alpha <<endl;
       TGeoTubeSeg *SL1 = new TGeoTubeSeg("SL1",swidth,r1346,hwidth+1.,5.,alpha-5.);
       TGeoTubeSeg *SL3 = new TGeoTubeSeg("SL3",swidth,r1346,hwidth+1.,180-alpha+5.,175.);
       TGeoTubeSeg *SL4 = new TGeoTubeSeg("SL4",swidth,r1346,hwidth+1.,185.,180.+alpha-5.);
       TGeoTubeSeg *SL6 = new TGeoTubeSeg("SL6",swidth,r1346,hwidth+1.,360.-alpha+5.,355.);
       TGeoTubeSeg *SL2 = new TGeoTubeSeg("SL2",swidth,r25,hwidth+1.,alpha+5.,180-alpha-5.);
       TGeoTubeSeg *SL5 = new TGeoTubeSeg("SL5",swidth,r25,hwidth+1.,180.+alpha+5.,360.-alpha-5.);
       TGeoRotation *r = new TGeoRotation("r"); r->RotateY(90.); r->RegisterYourself();

       TGeoCompositeShape *TS = new TGeoCompositeShape("TS",\
        "ms-FL1-FL2-FL3-FL4-FL5-FL6-SL1:r-SL2:r-SL3:r-SL4:r-SL5:r-SL6:r");
       
       TGeoVolume *T = new TGeoVolume("TSUP", TS, material); 
       T->SetLineColor(colour);      
       return T;
}
void ShipMagnet::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("iron");
    TGeoMedium *Fe =gGeoManager->GetMedium("iron");
    InitMedium("Aluminum");
    TGeoMedium *Al =gGeoManager->GetMedium("Aluminum");
    TGeoVolumeAssembly *tMagnet = new TGeoVolumeAssembly("SHiPMagnet");
    top->AddNode(tMagnet, 1, new TGeoTranslation(0, 0, 0));

    Double_t cm  = 1;       
    Double_t m   = 100*cm;  
    if (fDesign==1){
    // magnet yoke
     TGeoBBox *magyoke1 = new TGeoBBox("magyoke1", 350, 350, 125);
     TGeoBBox *magyoke2 = new TGeoBBox("magyoke2", 250, 250, 126);
    
     TGeoCompositeShape *magyokec = new TGeoCompositeShape("magyokec", "magyoke1-magyoke2");
     TGeoVolume *magyoke = new TGeoVolume("magyoke", magyokec, Fe);
     magyoke->SetLineColor(kBlue);
    //magyoke->SetTransparency(50);
     tMagnet->AddNode(magyoke, 1, new TGeoTranslation(0, 0, 1940));
    
    // magnet
     TGeoTubeSeg *magnet1a = new TGeoTubeSeg("magnet1a", 250, 300, 35, 45, 135);
     TGeoTubeSeg *magnet1b = new TGeoTubeSeg("magnet1b", 250, 300, 35, 45, 135);
     TGeoTubeSeg *magnet1c = new TGeoTubeSeg("magnet1c", 250, 270, 125, 45, 60);
     TGeoTubeSeg *magnet1d = new TGeoTubeSeg("magnet1d", 250, 270, 125, 120, 135);
    
    // magnet composite shape matrices
     TGeoTranslation *m1 = new TGeoTranslation(0, 0, 160);
     m1->SetName("m1");
     m1->RegisterYourself();
     TGeoTranslation *m2 = new TGeoTranslation(0, 0, -160);
     m2->SetName("m2");
     m2->RegisterYourself();
    
     TGeoCompositeShape *magcomp1 = new TGeoCompositeShape("magcomp1", "magnet1a:m1+magnet1b:m2+magnet1c+magnet1d");
     TGeoVolume *magnet1 = new TGeoVolume("magnet1", magcomp1, Fe);
     magnet1->SetLineColor(kYellow);
     tMagnet->AddNode(magnet1, 1, new TGeoTranslation(0, 0, fSpecMagz));  // was 1940
    
     TGeoRotation m3;
     m3.SetAngles(180, 0, 0);
     TGeoTranslation m4(0, 0, fSpecMagz);   // was 1940
     TGeoCombiTrans m5(m4, m3);
     TGeoHMatrix *m6 = new TGeoHMatrix(m5);
     tMagnet->AddNode(magnet1, 2, m6);
    }
    else if(fDesign==2 || fDesign==3) {  // fDesign==2 TP version, fDesign==3, rectangular version 
    Double_t Yokel = 1.25*m; 
    Double_t magnetIncrease = 100.*cm;
    // magnet yoke
    Double_t bradius = fDy/2.;
    TGeoBBox *magyoke1 = new TGeoBBox("magyoke1", fDx+0.7*m, bradius+1.2*m, Yokel);
    TGeoBBox *magyoke2 = new TGeoBBox("magyoke2", fDx-0.3*m, bradius+0.2*m, Yokel+0.01*cm);
    
    TGeoCompositeShape *magyokec = new TGeoCompositeShape("magyokec", "magyoke1-magyoke2");
    TGeoVolume *magyoke = new TGeoVolume("magyoke", magyokec, Fe);
    magyoke->SetLineColor(kBlue);
    tMagnet->AddNode(magyoke, 1, new TGeoTranslation(0, 0, fSpecMagz));

    Double_t hsupport=(10.*m-(bradius+1.2*m)-floorheight)/2.;
    TGeoVolume* SMS =MagnetSupport(fDx+0.7*m, hsupport, Yokel,15,Fe);
    tMagnet->AddNode(SMS, 1, new TGeoTranslation(0, -bradius-1.2*m-hsupport, fSpecMagz));

    //Attempt to make Al coils...
    TGeoCompositeShape *MCoilc;
    if(fDesign==2){
     TGeoEltu *C2  = new TGeoEltu("C2",fDx,bradius+0.5*m,Yokel+0.6*m+magnetIncrease/2.);
     TGeoEltu *C1  = new TGeoEltu("C1",fDx-0.3*m,bradius+0.2*m,Yokel+0.601*m+magnetIncrease/2.);
     TGeoBBox *Box1 = new TGeoBBox("Box1", 1.*m, bradius+0.51*m, Yokel+0.61*m+magnetIncrease/2.);
     TGeoBBox *Box2 = new TGeoBBox("Box2", fDx+0.01*m, bradius-0.5*m, Yokel+0.01*m+magnetIncrease/2.);
     MCoilc = new TGeoCompositeShape("MCoilc", "C2-C1-magyokec-Box1-Box2");
    }else{
     TGeoBBox *C2   = new TGeoBBox("C2",   fDx,        bradius+0.5*m,  Yokel+0.6*m+magnetIncrease/2.);
     TGeoBBox *C1   = new TGeoBBox("C1",   fDx-0.3*m,  bradius+0.2*m,  Yokel+0.601*m+magnetIncrease/2.);
     MCoilc = new TGeoCompositeShape("MCoilc", "C2-C1-magyokec");
    }
    TGeoVolume *MCoil = new TGeoVolume("MCoil", MCoilc, Al);
    MCoil->SetLineColor(kYellow);
   
    tMagnet->AddNode(MCoil, 1, new TGeoTranslation(0, 0, fSpecMagz));

    }else if(fDesign==4) {  // rectangular a la MISIS, full opening for vessel
     //define dimensions
     Double_t xaperture=fDx;  //half apertures
     Double_t yaperture=fDy;  
     //built the yoke
     TGeoBBox *magyoke1 = new TGeoBBox("magyoke1", xaperture+YokeWidth,yaperture+YokeWidth,YokeDepth);
     TGeoBBox *magyoke2 = new TGeoBBox("magyoke2", xaperture,yaperture,YokeDepth+1.);    
     TGeoCompositeShape *magyokec = new TGeoCompositeShape("magyokec", "magyoke1-magyoke2");
     //and a epsilon larger yoke to subtract while making the coils
     TGeoBBox *my1 = new TGeoBBox("my1", xaperture+YokeWidth,yaperture+YokeWidth,YokeDepth+0.1*cm);
     TGeoBBox *my2 = new TGeoBBox("my2", xaperture-0.1*cm,yaperture-0.1*cm,YokeDepth+1.);    
     TGeoCompositeShape *myc = new TGeoCompositeShape("myc", "my1-my2");
     TGeoVolume *magyoke = new TGeoVolume("magyoke", magyokec, Fe);
     magyoke->SetLineColor(kBlue);
     tMagnet->AddNode(magyoke, 1, new TGeoTranslation(0, 0, fSpecMagz));
     //and the coils: top
     TGeoTubeSeg *CTop = new TGeoTubeSeg("CTop",1.*cm,YokeWidth,YokeDepth+CoilThick+1.*cm,0.,180.);
     TGeoTranslation *t1 = new TGeoTranslation("t1",xaperture,yaperture-CoilThick,0.); t1->RegisterYourself();
     TGeoTranslation *t2 = new TGeoTranslation("t2",-xaperture,yaperture-CoilThick,0.); t2->RegisterYourself();
     TGeoCompositeShape *CTop1 = new TGeoCompositeShape("CTop1", "CTop:t1-myc");
     TGeoCompositeShape *CTop2 = new TGeoCompositeShape("CTop2", "CTop:t2-myc");
     TGeoVolume *MCoil1 = new TGeoVolume("MCoil1", CTop1, Al);
     TGeoVolume *MCoil2 = new TGeoVolume("MCoil2", CTop2, Al);
     MCoil1->SetLineColor(kYellow);   
     tMagnet->AddNode(MCoil1, 1, new TGeoTranslation(0, 0, fSpecMagz));
     MCoil2->SetLineColor(kYellow);   
     tMagnet->AddNode(MCoil2, 1, new TGeoTranslation(0, 0, fSpecMagz));
     //coils bottom
     TGeoTubeSeg *CBot = new TGeoTubeSeg("CBot",1.*cm,YokeWidth,YokeDepth+CoilThick+1.*cm,180.,360.);
     TGeoTranslation *b1 = new TGeoTranslation("b1",xaperture,-yaperture+CoilThick,0.); b1->RegisterYourself();
     TGeoTranslation *b2 = new TGeoTranslation("b2",-xaperture,-yaperture+CoilThick,0.); b2->RegisterYourself();
     TGeoCompositeShape *CBot1 = new TGeoCompositeShape("CBot1", "CBot:b1-myc");
     TGeoCompositeShape *CBot2 = new TGeoCompositeShape("CBot2", "CBot:b2-myc");
     TGeoVolume *MCoil3 = new TGeoVolume("MCoil3", CBot1, Al);
     TGeoVolume *MCoil4 = new TGeoVolume("MCoil4", CBot2, Al);
     MCoil3->SetLineColor(kYellow);   
     tMagnet->AddNode(MCoil3, 1, new TGeoTranslation(0, 0, fSpecMagz));
     MCoil4->SetLineColor(kYellow);   
     tMagnet->AddNode(MCoil4, 1, new TGeoTranslation(0, 0, fSpecMagz));
     //add vertical coils
     TGeoBBox *CVert = new TGeoBBox("CVert",YokeWidth/2.,yaperture-CoilThick,CoilThick/2.);
     TGeoVolume *CV = new TGeoVolume("CV", CVert, Al);
     CV->SetLineColor(kYellow);   
     tMagnet->AddNode(CV, 1, new TGeoTranslation(xaperture+YokeWidth/2., 0, fSpecMagz-YokeDepth-CoilThick/2.));
     tMagnet->AddNode(CV, 2, new TGeoTranslation(-xaperture-YokeWidth/2., 0, fSpecMagz-YokeDepth-CoilThick/2.));
     tMagnet->AddNode(CV, 3, new TGeoTranslation(xaperture+YokeWidth/2., 0, fSpecMagz+YokeDepth+CoilThick/2.));
     tMagnet->AddNode(CV, 4, new TGeoTranslation(-xaperture-YokeWidth/2., 0, fSpecMagz+YokeDepth+CoilThick/2.));
     

    }
}



ClassImp(ShipMagnet)














