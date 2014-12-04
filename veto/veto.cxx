#include "veto.h"

#include "vetoPoint.h"


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
#include "TGeoBoolNode.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
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
    fT0z(-2390.),              //!  z-position of veto station
    fT1z(1510.),               //!  z-position of tracking station 1
    fT2z(1710.),               //!  z-position of tracking station 2
    fT3z(2150.),               //!  z-position of tracking station 3
    fT4z(2370.),               //!  z-position of tracking station 4
    fRmin(249.),               //!  inner radius of vacuumtank
    fRmax(250.),               //!  outer radius of vacuumtank
    fVRmin(250.5),               //!  inner radius of liquid scintillator
    fVRmax(259.5),               //!  outer radius of liquid scintillator
    fvetoPointCollection(new TClonesArray("vetoPoint"))
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
// private method create ellipsoids
void veto::GeoEllipticalTube(const char* name,Double_t thick,Double_t a,Double_t b,Double_t dz,Double_t z,Int_t colour,TGeoMedium *material,Bool_t sens=false)
{
  /*make elliptical tube by subtraction
   tick is wall thickness
   a,b are inner ellipse radii, dz is the half-length
   will be put at z, with colour and material*/
       TGeoVolume *top = gGeoManager->GetTopVolume();
       TGeoEltu *T2  = new TGeoEltu("T2",a+thick,b+thick,dz);
       TGeoEltu *T1  = new TGeoEltu("T1",a,b,dz+0.1);
       TGeoSubtraction *subtraction = new TGeoSubtraction(T2,T1);
       TGeoCompositeShape *Tc = new TGeoCompositeShape(name, subtraction);
       TGeoVolume *T = new TGeoVolume(name, Tc, material);

       T->SetLineColor(colour);
       top->AddNode(T, 1, new TGeoTranslation(0, 0, z));
       //and make the volunes sensitive..
       if (sens) {AddSensitiveVolume(T);}
}
// private method create plate with ellips hole in the center
void veto::GeoPlateEllipse(const char* name,Double_t thick,Double_t a,Double_t b,Double_t dz,Double_t z,Int_t colour,TGeoMedium *material)
{
  /*make plate with elliptical hole.
   plate has half width/height: a(b)+thick
   a,b are ellipse radii of hole, dz is the half-thickness of the plate
   will be put at z, with colour and material*/
       TGeoVolume *top = gGeoManager->GetTopVolume();
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
void veto::SetTubZpositions(Double32_t z1, Double32_t z2, Double32_t z3, Double32_t z4, Double32_t z5, Double32_t z6)
{
     fTub1z = z1;                                                 //!  z-position of tub1
     fTub2z = z2;                                                 //!  z-position of tub2
     fTub3z = z3;                                                 //!  z-position of tub3
     fTub4z = z4;                                                 //!  z-position of tub4
     fTub5z = z5;                                                 //!  z-position of tub5
     fTub6z = z6;                                                 //!  z-position of tub6
}

void veto::SetTublengths(Double32_t l1, Double32_t l2, Double32_t l3, Double32_t l4, Double32_t l5, Double32_t l6)
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
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode);

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
void veto::SetZpositions(Double32_t z0, Double32_t z1, Double32_t z2, Double32_t z3, Double32_t z4, Int_t c)
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
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("steel");
    TGeoMedium *St =gGeoManager->GetMedium("steel");
    InitMedium("vacuums");
    TGeoMedium *vac =gGeoManager->GetMedium("vacuums");
    InitMedium("Aluminum");
    TGeoMedium *Al =gGeoManager->GetMedium("Aluminum");
    InitMedium("ShipSens");
    InitMedium("Scintillator");
    TGeoMedium *Se =gGeoManager->GetMedium("Scintillator");
    gGeoManager->SetNsegments(100);
    if (fDesign !=2 && fDesign<4)
    { 
    // entrance window
     TGeoVolume *enWin = gGeoManager->MakeTube("enWin", St, 0, fRmax, fRmax-fRmin);
     enWin->SetLineColor(18);  // silver/gray
     top->AddNode(enWin, 1, new TGeoTranslation(0, 0, fTub1z-2*fTub1length-0.1));
     AddSensitiveVolume(enWin);
    // first part of vacuum chamber up to veto station
     TGeoVolume *tub1  = gGeoManager->MakeTube("tub1",  St, fRmin,  fRmax,  fTub1length);
     TGeoVolume *stub1 = gGeoManager->MakeTube("stub1", Se, fVRmin, fVRmax, fTub1length);
     TGeoVolume *vtub1 = gGeoManager->MakeTube("vtub1", vac, 0,     fRmin,  fTub1length);
     tub1->SetLineColor(18);  // silver/gray
     vtub1->SetVisibility(kFALSE);
     vtub1->SetTransparency(1);
     stub1->SetLineColor(kMagenta-10);
     TGeoTranslation* tv1 = new TGeoTranslation(0, 0, fTub1z);
     top->AddNode(tub1,  1,  tv1);    
     top->AddNode(vtub1, 1,  tv1);    
     top->AddNode(stub1, 1,  tv1);
     AddSensitiveVolume(stub1);
    // second part of vacuum chamber up to first tracking station
     TGeoVolume *tub2 =  gGeoManager->MakeTube("tub2",  St, fRmin,  fRmax,  fTub2length);
     TGeoVolume *stub2 = gGeoManager->MakeTube("stub2", Se, fVRmin, fVRmax, fTub2length);
     TGeoVolume *vtub2 = gGeoManager->MakeTube("vtub2", vac, 0,     fRmin,  fTub2length);
     tub2->SetLineColor(18);
     vtub2->SetVisibility(kFALSE);
     vtub2->SetTransparency(1);
     stub2->SetLineColor(kMagenta-10);
     TGeoTranslation* tv2 = new TGeoTranslation(0, 0, fTub2z);
     top->AddNode(tub2,  1, tv2);
     top->AddNode(stub2, 1, tv2);
     top->AddNode(vtub2, 1, tv2);
     AddSensitiveVolume(stub2);
    }else if (fDesign<4){
    // conical design
    // entrance window
     TGeoVolume *enWin = gGeoManager->MakeTube("enWin", St, 0, 100, fRmax-fRmin);
     enWin->SetLineColor(18);  // silver/gray
     top->AddNode(enWin, 1, new TGeoTranslation(0, 0, fTub1z-2*fTub1length-0.1));
     AddSensitiveVolume(enWin);
    // first part of vacuum chamber up to first tracking station, conical design
     Double_t length = (fTub2z + fTub2length - (fTub1z-fTub1length))/2. ;
     Double_t z      = (fTub1z-fTub1length) - length ;
     TGeoVolume *tub2   = gGeoManager->MakeCone("tub2",  St,  length,100,102,fRmin,fRmax);  
     TGeoVolume *stub2  = gGeoManager->MakeCone("stub2", Se,  length,101,110,fRmin+1.,fRmax+9.);   
     TGeoVolume *vtub2  = gGeoManager->MakeCone("vtub2", vac, length,0,100,0,fRmin);   
     tub2->SetLineColor(18);
     vtub2->SetVisibility(kFALSE);
     stub2->SetLineColor(kMagenta-10);
     TGeoTranslation* tv2 = new TGeoTranslation(0, 0, z);
     top->AddNode(tub2, 1,  tv2);
     top->AddNode(vtub2, 1, tv2);
     AddSensitiveVolume(tub2);

    // third part of vacuum chamber up to second tracking station
    TGeoVolume *tub3  = gGeoManager->MakeTube("tub3", St,  fRmin, fRmax, fTub3length);
    TGeoVolume *vtub3 = gGeoManager->MakeTube("vtub3", vac, 0, fRmin, fTub3length);
    tub3->SetLineColor(18);
    vtub3->SetVisibility(kFALSE);
    TGeoTranslation* tv3 = new TGeoTranslation(0, 0, fTub3z);
    top->AddNode(tub3, 1,  tv3);
    top->AddNode(vtub3, 1, tv3);
    AddSensitiveVolume(tub3);
    
    // fourth part of vacuum chamber up to third tracking station and being covered by magnet
    TGeoVolume *tub4 = gGeoManager->MakeTube("tub4", St,  fRmin, fRmax, fTub4length);
    TGeoVolume *vtub4 = gGeoManager->MakeTube("vtub4", vac, 0, fRmin, fTub4length);
    tub4->SetLineColor(18);
    vtub4->SetVisibility(kFALSE);
    TGeoTranslation* tv4 = new TGeoTranslation(0, 0, fTub4z);
    top->AddNode(tub4, 1,  tv4);
    top->AddNode(vtub4, 1, tv4);
    
    // fifth part of vacuum chamber up to fourth tracking station
    TGeoVolume *tub5 = gGeoManager->MakeTube("tub5", St,  fRmin, fRmax,fTub5length);
    TGeoVolume *vtub5 = gGeoManager->MakeTube("vtub5", vac, 0, fRmin,fTub5length);
    vtub5->SetVisibility(kFALSE);
    tub5->SetLineColor(18);
    TGeoTranslation* tv5 = new TGeoTranslation(0, 0, fTub5z);
    top->AddNode(tub5, 1,  tv5);
    top->AddNode(vtub5, 1, tv5);
    
    // sixth part of vacuum chamber up to Ecal detector
    TGeoVolume *tub6 = gGeoManager->MakeTube("tub6", St,  fRmin, fRmax, 20);
    TGeoVolume *vtub6 = gGeoManager->MakeTube("vtub6", St, 0, fRmin, 20);
    vtub6->SetVisibility(kFALSE);
    tub6->SetLineColor(18);
    TGeoTranslation* tv6 = new TGeoTranslation(0, 0, fTub6z);
    top->AddNode(tub6, 1, tv6);
    top->AddNode(vtub6, 1,tv6);
    }  // 
  // here the standard tracking stations 
    if (fDesign==1){
 // with conical shape of decay tube, previous veto station does not make so much sense anymore
     TGeoBBox *vdetbox1 = new TGeoBBox("vdetbox1", fRmax, fRmax, 10);
     TGeoBBox *vdetbox2 = new TGeoBBox("vdetbox2", fRmax-5., fRmax-5., 10);
     TGeoBBox *vdetSens = new TGeoBBox("vdetSens", fRmax-6., fRmax-6., 1);   
     TGeoCompositeShape *vdetcomp1 = new TGeoCompositeShape("vdetcomp1", "vdetbox1-vdetbox2");
     TGeoVolume *det1 = new TGeoVolume("vetoX", vdetcomp1, Al);
     det1->SetLineColor(kRed);
     top->AddNode(det1, 1, new TGeoTranslation(0, 0, fT0z));
    
     for (Int_t i=0; i<4; i++) {
      TString nm = "Sveto_"; nm += i;
      TGeoVolume *Sdet = new TGeoVolume(nm, vdetSens, Se);
      top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT0z-4+i*2.));
      AddSensitiveVolume(Sdet);
     }

     TGeoRotation r0;
     r0.SetAngles(15,0,0);
     TGeoTranslation t0(0, 0, fT0z+20);
     TGeoCombiTrans c0(t0, r0);
     TGeoHMatrix *h0 = new TGeoHMatrix(c0);
     TGeoVolume *det2 = new TGeoVolume("vetoS", vdetcomp1, Al);
     det2->SetLineColor(kRed);
     top->AddNode(det2, 11, h0);
    }
    if (fDesign<3){
    // with design 3, detailed implementation of strawchambers exist, no need for this basic layout
     TGeoBBox *detbox1 = new TGeoBBox("detbox1", fRmax, fRmax, 10);
     TGeoBBox *detbox2 = new TGeoBBox("detbox2", fRmax-5., fRmax-5., 10);
     TGeoBBox *detSens = new TGeoBBox("detSens", fRmax-6., fRmax-6., 1);   
     TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");
     // tracking station 1
     TGeoVolume *det3 = new TGeoVolume("Tr1X", detcomp1, Al);
     det3->SetLineColor(kRed-7);
     top->AddNode(det3, 2, new TGeoTranslation(0, 0, fT1z));
     TGeoRotation r1;
     r1.SetAngles(15,0,0);
     TGeoTranslation t1(0, 0, fT1z+20);
     TGeoCombiTrans c1(t1, r1);
     TGeoHMatrix *h1 = new TGeoHMatrix(c1);
     TGeoVolume *det4 = new TGeoVolume("Tr1S", detcomp1, Al);
     det4->SetLineColor(kRed+2);
     top->AddNode(det4, 3, h1);

     for (Int_t i=0; i<4; i++) {
      TString nm = "STr1_"; nm += i;
      TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
      top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT1z-4+i*2));
      AddSensitiveVolume(Sdet);
     }
    // tracking station 2
     TGeoVolume *det5 = new TGeoVolume("Tr2X", detcomp1, Al);
     det5->SetLineColor(kRed-7);
     top->AddNode(det5, 4, new TGeoTranslation(0, 0, fT2z));
     TGeoRotation r2;
     r2.SetAngles(15,0,0);
     TGeoTranslation t2(0, 0, fT2z+20);
     TGeoCombiTrans c2(t2, r2);
     TGeoHMatrix *h2 = new TGeoHMatrix(c2);
     TGeoVolume *det6 = new TGeoVolume("Tr2S", detcomp1, Al);
     det4->SetLineColor(kRed+2);
     top->AddNode(det6, 5, h2);
     for (Int_t i=0; i<4; i++) {
      TString nm = "STr2_"; nm += i;
      TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
      top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT2z-4+i*2));
      AddSensitiveVolume(Sdet);
     }
    // tracking station 3
     TGeoVolume *det7 = new TGeoVolume("Tr3X", detcomp1, Al);
     det7->SetLineColor(kOrange+10);
     top->AddNode(det7, 6, new TGeoTranslation(0, 0, fT3z));
     TGeoRotation r3;
     r3.SetAngles(15,0,0);
     TGeoTranslation t3(0, 0, fT3z+20);
     TGeoCombiTrans c3(t3, r3);
     TGeoHMatrix *h3 = new TGeoHMatrix(c3);
     TGeoVolume *det8 = new TGeoVolume("Tr3S", detcomp1, Al);
     det8->SetLineColor(kOrange+4);
     top->AddNode(det8, 7, h3);
     for (Int_t i=0; i<4; i++) {
      TString nm = "STr3_"; nm += i;
      TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
      top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT3z-4+i*2));
      AddSensitiveVolume(Sdet);
     }   
    // tracking station 4
     TGeoVolume *det9 = new TGeoVolume("Tr4X", detcomp1, Al);
     det9->SetLineColor(kOrange+10);
     top->AddNode(det9, 8, new TGeoTranslation(0, 0, fT4z));
     TGeoRotation r4;
     r4.SetAngles(15,0,0);
     TGeoTranslation t4(0, 0, fT4z+20);
     TGeoCombiTrans c4(t4, r4);
     TGeoHMatrix *h4 = new TGeoHMatrix(c4);
     TGeoVolume *det10 = new TGeoVolume("Tr4S", detcomp1, Al);
     det10->SetLineColor(kOrange+4);
     top->AddNode(det10, 9, h4);
     for (Int_t i=0; i<4; i++) {
      TString nm = "STr4_"; nm += i;
      TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
      top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT4z-4+i*2));
      AddSensitiveVolume(Sdet);
     }
    }   
    if (fDesign==4){

    // design 4: elliptical double walled tube with LiSci in between
    // Interpolate wall thicknesses based on the vertical size fBtube.
      Double_t walli=(fBtube-6.*m)*(8.-5.)*mm/(4.*m)+3.*mm;	
      Double_t wallo=(fBtube-6.*m)*(3.-2.)*cm/(4.*m)+2.*cm;	
      Double_t ws=0.5*m; //Straw screen plates sticking out of the outer tube.
      //Note: is just 2 cm for veto chamber, to avoid muon hits :-).
      Double_t liscitube=0.1*m;	
      Double_t liscilid=0.2*m;	
      Double_t atube=2.5*m;	
      Double_t btube = fBtube;
      Double_t atube1=2.2*m-walli-wallo-liscitube;	
      //inner lid on tube 1
      TGeoVolume *lidT1I = gGeoManager->MakeEltu("lidT1I",Al,atube1+walli,btube+walli,walli/2.);
      lidT1I->SetLineColor(kRed);  // silver/gray
      top->AddNode(lidT1I, 1, new TGeoTranslation(0, 0, fTub1z-fTub1length-walli/2.));
      //lisci lid on tube 1
      TGeoVolume *lidT1lisci = gGeoManager->MakeEltu("lidT1lisci",Se,atube1+walli+liscitube,btube+walli+liscitube,liscilid/2.);
      lidT1lisci->SetLineColor(kMagenta-10);
      top->AddNode(lidT1lisci, 1, new TGeoTranslation(0, 0, fTub1z-fTub1length-walli-liscilid/2.));
      AddSensitiveVolume(lidT1lisci);
      //outer lid on tube 1
      TGeoVolume *lidT1O = gGeoManager->MakeEltu("lidT1O",St,atube1+walli+wallo+liscitube,btube+walli+wallo+liscitube,wallo/2.);
      lidT1O->SetLineColor(18);  // silver/gray
      top->AddNode(lidT1O, 1, new TGeoTranslation(0, 0, fTub1z-fTub1length-walli-liscilid-wallo/2.));

      // All inner tubes...
      GeoEllipticalTube("T1I",walli,atube1,btube,fTub1length,fTub1z,kRed,Al);
      GeoEllipticalTube("T2I",walli,atube,btube,fTub2length,fTub2z,kRed,Al);
      GeoEllipticalTube("T3I",walli,atube,btube,fTub3length,fTub3z,kRed,Al);
      GeoEllipticalTube("T4I",walli,atube,btube,fTub4length,fTub4z,kRed,Al);
      GeoEllipticalTube("T5I",walli,atube,btube,fTub5length,fTub5z,kRed,Al);
      GeoEllipticalTube("T6I",walli,atube,btube,fTub6length,fTub6z,kRed,Al);
      // All outer tubes, first calculate inner radii of this tube
      Double_t aO=atube+walli+liscitube;
      Double_t aO1=atube1+walli+liscitube;
      Double_t bO=btube+walli+liscitube;
      GeoEllipticalTube("T1O",wallo,aO1,bO,fTub1length+liscilid/2,fTub1z-liscilid/2,18,St);
      GeoPlateEllipse("T1Endplate",0.02*m+(atube-atube1),aO1+wallo,bO+wallo,wallo/2.,fTub1z+fTub1length-wallo/2.,18,St);
      GeoEllipticalTube("T2O",wallo,aO,bO,fTub2length,fTub2z,18,St);
      GeoPlateEllipse("T2Startplate",0.02*m,aO+wallo,bO+wallo,wallo/2.,fTub2z-fTub2length+wallo/2.,18,St);
      GeoPlateEllipse("T2Endplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub2z+fTub2length-wallo/2.,18,St);
      GeoEllipticalTube("T3O",wallo,aO,bO,fTub3length,fTub3z,18,St);
      GeoPlateEllipse("T3Startplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub3z-fTub3length+wallo/2.,18,St);
      GeoPlateEllipse("T3Endplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub3z+fTub3length-wallo/2.,18,St);
      GeoEllipticalTube("T4O",wallo,aO,bO,fTub4length,fTub4z,18,St);
      GeoPlateEllipse("T4Startplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub4z-fTub4length+wallo/2.,18,St);
      GeoPlateEllipse("T4Endplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub4z+fTub4length-wallo/2.,18,St);
      GeoEllipticalTube("T5O",wallo,aO,bO,fTub5length,fTub5z,18,St);
      GeoPlateEllipse("T5Startplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub5z-fTub5length+wallo/2.,18,St);
      GeoPlateEllipse("T5Endplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub5z+fTub5length-wallo/2.,18,St);
      GeoEllipticalTube("T6O",wallo,aO,bO,fTub6length+liscilid/2.,fTub6z+liscilid/2.,18,St);
      GeoPlateEllipse("T6Startplate",ws,aO+wallo,bO+wallo,wallo/2.,fTub6z-fTub6length+wallo/2.,18,St);
      // And liquid scintillator inbetween, first calculate inner radii of this
      Double_t als=atube+walli;
      Double_t als1=atube1+walli;
      Double_t bls=btube+walli;
      GeoEllipticalTube("T1LS",liscitube,als1,bls,fTub1length,fTub1z,kMagenta-10,Se,true);
      GeoEllipticalTube("T2LS",liscitube,als,bls,fTub2length,fTub2z,kMagenta-10,Se,true);
      GeoEllipticalTube("T3LS",liscitube,als,bls,fTub3length,fTub3z,kMagenta-10,Se,true);
      GeoEllipticalTube("T4LS",liscitube,als,bls,fTub4length,fTub4z,kMagenta-10,Se,true);
      GeoEllipticalTube("T5LS",liscitube,als,bls,fTub5length,fTub5z,kMagenta-10,Se,true);
      GeoEllipticalTube("T6LS",liscitube,als,bls,fTub6length,fTub6z,kMagenta-10,Se,true);

      //closing lid on tube 6
      TGeoVolume *lidT6I = gGeoManager->MakeEltu("lidT6I",Al,atube+walli,btube+walli,walli/2.);
      lidT6I->SetLineColor(kRed);  // silver/gray
      top->AddNode(lidT6I, 1, new TGeoTranslation(0, 0, fTub6z+fTub6length+walli/2.));
      //lisci lid on tube 6
      TGeoVolume *lidT6lisci = gGeoManager->MakeEltu("lidT6lisci",Se,atube+walli+liscitube,btube+walli+liscitube,liscilid/2.);
      lidT6lisci->SetLineColor(kMagenta-10);
      top->AddNode(lidT6lisci, 1, new TGeoTranslation(0, 0, fTub6z+fTub6length+walli+liscilid/2.));
      AddSensitiveVolume(lidT6lisci);
      //outer lid on tube 1
      TGeoVolume *lidT6O = gGeoManager->MakeEltu("lidT6O",St,atube+walli+wallo+liscitube,btube+walli+wallo+liscitube,wallo/2.);
      lidT6O->SetLineColor(18);  // silver/gray
      top->AddNode(lidT6O, 1, new TGeoTranslation(0, 0, fTub6z+fTub6length+walli+liscilid+wallo/2.));

      //Add one more sensitive plane after vacuum tube for timing
      TGeoVolume *TimeDet = gGeoManager->MakeBox("TimeDet",Se,atube+walli+wallo+liscitube,btube+walli+wallo+liscitube,liscilid/2.);
      TimeDet->SetLineColor(kMagenta-10);
      top->AddNode(TimeDet, 1, new TGeoTranslation(0, 0, fTub6z+fTub6length+walli+liscilid*1.5+wallo+5.*cm));
      AddSensitiveVolume(TimeDet);

      //Add  rough nu-tau Mu-Spec...
      Double_t ZGmid=fTub1z-fTub1length-walli-liscilid-wallo-7.4*m;
      Double_t sz = ZGmid+2.25*m+0.2*m+2.45*m;
      Double_t dIronOpera= 0.3*m;

      //Add one sensitive plane in middle of Goliath
      TGeoVolume *Emulsion = gGeoManager->MakeBox("Emulsion", Se, 0.5*m, 0.5*m, 5.*cm);
      Emulsion->SetLineColor(kMagenta-10);
      top->AddNode(Emulsion, 1, new TGeoTranslation(0, 0, ZGmid));
      AddSensitiveVolume(Emulsion);

      //Add one sensitive plane after nu-tau mu-shield
      // now taken care by volDriftLayer and volDriftLayer1-5
      //TGeoVolume *DetMuNuTau = gGeoManager->MakeBox("DetMuNuTau", Se, 2.5*m, 5.*m, 5.*cm);
      //DetMuNuTau->SetLineColor(kMagenta-10);
      //top->AddNode(DetMuNuTau, 1, new TGeoTranslation(0, 0, sz+0.91*m+dIronOpera+50.*cm));       
      //AddSensitiveVolume(DetMuNuTau);


      //Add one sensitive plane counting rate in second detector downstream
      // with shielding around, 
      Double_t thickness = 10.*cm /2.;
      TGeoBBox *shield2Out = new TGeoBBox("shield2Out",2.5*m+thickness, 3*m+thickness, 20.*cm+thickness);
      TGeoBBox *shield2In  = new TGeoBBox("shield2In", 2.5*m+0.1*cm, 3*m+0.1*cm, 20.*cm+0.1*cm);
      TGeoCompositeShape *shieldDet2 = new TGeoCompositeShape("shieldDet2", "shield2Out-shield2In");
      TGeoVolume *sdet2 = new TGeoVolume("shieldDet2", shieldDet2, St);
      sdet2->SetLineColor(kWhite-5);
      top->AddNode(sdet2, 1, new TGeoTranslation(0, 0, fTub6z + 50.*m));
      TGeoVolume *Det2 = gGeoManager->MakeBox("Det2", Se, 2.5*m, 3.*m, 5.*cm);
      Det2->SetLineColor(kGreen+3);
      top->AddNode(Det2, 1, new TGeoTranslation(0, 0, fTub6z + 50.*m));       
      AddSensitiveVolume(Det2);
     }
}

vetoPoint* veto::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode)
{
  TClonesArray& clref = *fvetoPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "veto hit called "<< pos.z()<<endl;
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode);
}

ClassImp(veto)
