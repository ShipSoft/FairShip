#include "veto.h"

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
    fFastMuon(false),
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
void veto::GeoEllipticalTube(const char* name,Double_t thick,Double_t a,Double_t b,Double_t dz,Double_t z,Int_t colour,TGeoMedium *material,TGeoVolume *top,Bool_t sens=false)
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
       top->AddNode(T, 1, new TGeoTranslation(0, 0, z));
       //and make the volunes sensitive..
       if (sens) {AddSensitiveVolume(T);}
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
    TLorentzVector Pos; 
    gMC->TrackPosition(Pos); 
    Double_t xmean = (fPos.X()+Pos.X())/2. ;      
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean),
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
    if (fDesign!=4){ fLogger->Fatal(MESSAGE_ORIGIN, "Only Design 4 is supported!");}
    else { 
    // put everything in an assembly
      TGeoVolume *tDecayVol = new TGeoVolumeAssembly("DecayVolume");
      TGeoVolume *tMaGVol   = new TGeoVolumeAssembly("MagVolume");
    // design 4: elliptical double walled tube with LiSci in between
    // Interpolate wall thicknesses based on the vertical size fBtube.
      // for Y=10m: 
      Double_t walli=3.*cm; 
      Double_t wallo=8.*mm;
      // ignore variations with height
      //Double_t wallo=(2*fBtube-6.*m)*(8.-5.)*mm/(4.*m)+5.*mm;	
      //Double_t walli=(2*fBtube-6.*m)*(3.-2.)*cm/(4.*m)+2.*cm;	
      
      Double_t ws=0.5*m; //Straw screen plates sticking out of the outer tube.
      //Note: is just 2 cm for veto chamber, to avoid muon hits :-).
      Double_t liscitube= 0.3*m;	
      //Double_t liscilid = 0.2*m;	
      Double_t atube    = 2.5*m;	
      Double_t btube    = fBtube;
      Double_t atube1   = 2.2*m-walli-wallo-liscitube;	
      Double_t zStartDecayVol = fTub1z-fTub1length-walli;
      Double_t zStartMagVol = fTub3z+fTub3length-walli;
      
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
      GeoEllipticalTube("T1I",walli,atube1,btube,fTub1length,fTub1z - zStartDecayVol,18,St,tDecayVol);
      GeoEllipticalTube("T2I",walli,atube, btube,fTub2length,fTub2z - zStartDecayVol,18,St,tDecayVol);
      GeoEllipticalTube("T3I",walli,atube, btube,fTub3length,fTub3z - zStartMagVol,18,St,tMaGVol);
      GeoEllipticalTube("T4I",walli,atube, btube,fTub4length,fTub4z - zStartMagVol,18,St,tMaGVol);
      GeoEllipticalTube("T5I",walli,atube, btube,fTub5length,fTub5z - zStartMagVol,18,St,tMaGVol);
      GeoEllipticalTube("T6I",walli,atube, btube,fTub6length,fTub6z - zStartMagVol,18,St,tMaGVol);
      // All outer tubes, first calculate inner radii of this tube
      Double_t aO =atube+walli+liscitube;
      Double_t aO1=atube1+walli+liscitube;
      Double_t bO =btube+walli+liscitube;
      GeoEllipticalTube("T1O",wallo,aO1,bO,fTub1length,fTub1z - zStartDecayVol,14,Al,tDecayVol);
      GeoEllipticalTube("T2O",wallo,aO, bO,fTub2length,fTub2z - zStartDecayVol,14,Al,tDecayVol);
      GeoEllipticalTube("T3O",wallo,aO, bO,fTub3length,fTub3z - zStartDecayVol,14,Al,tDecayVol);
      GeoEllipticalTube("T5O",wallo,aO, bO,fTub5length,fTub5z - zStartDecayVol,14,Al,tDecayVol);
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

      //For Tube nr 1:
      Int_t nribs = 2+fTub1length*2./(1.*m) ;
      Double_t ribspacing = (fTub1length*2.-nribs*walli)/(nribs-1)+walli;
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        TString namerib = "T1Rib_"; namerib+=nr;
        Double_t zrib= fTub1z-fTub1length+walli/2.+nr*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als1,bls,walli/2.,zrib- zStartDecayVol,18,St,tDecayVol);
      }
      //now place LiSc
      for (Int_t nr=1; nr<nribs; nr++) {
        TString namerib = "T1LiSc_"; namerib+=nr;
        Double_t zlength=(ribspacing-walli)/2.;
        Double_t zlisc= fTub1z-fTub1length+walli+zlength+(nr-1)*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als1,bls,zlength,zlisc- zStartDecayVol,kMagenta-10,Se,tDecayVol,true);
      }

      //For Tube nr 2:
      nribs = 2+fTub2length*2./(1.*m) ;
      ribspacing = (fTub2length*2.-nribs*walli)/(nribs-1)+walli;
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        TString namerib = "T2Rib_"; namerib+=nr;
        Double_t zrib= fTub2z-fTub2length+walli/2.+nr*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als,bls,walli/2.,zrib- zStartDecayVol,18,St,tDecayVol);
      }
      //now place LiSc
      for (Int_t nr=1; nr<nribs; nr++) {
        TString namerib = "T2LiSc_"; namerib+=nr;
        Double_t zlength=(ribspacing-walli)/2.;
        Double_t zlisc=fTub2z-fTub2length+walli+zlength+(nr-1)*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als,bls,zlength,zlisc-zStartDecayVol,kMagenta-10,Se,tDecayVol,true);
      }

      //For Tube nr 3:
      nribs = 2+fTub3length*2./(1.*m) ;
      ribspacing = (fTub3length*2.-nribs*walli)/(nribs-1)+walli;
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        TString namerib = "T3Rib_"; namerib+=nr;
        Double_t zrib= fTub3z-fTub3length+walli/2.+nr*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als,bls,walli/2.,zrib- zStartDecayVol,18,St,tDecayVol);
      }
      //now place LiSc
      for (Int_t nr=1; nr<nribs; nr++) {
        TString namerib = "T3LiSc_"; namerib+=nr;
        Double_t zlength=(ribspacing-walli)/2.;
        Double_t zlisc=fTub3z-fTub3length+walli+zlength+(nr-1)*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als,bls,zlength,zlisc-zStartDecayVol,kMagenta-10,Se,tDecayVol,true);
      }

      //For Tube nr 4:
      nribs = 2+fTub4length*2./(1.*m) ;
      ribspacing = (fTub4length*2.-nribs*walli)/(nribs-1)+walli;
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        TString namerib = "T4Rib_"; namerib+=nr;
        Double_t zrib= fTub4z-fTub4length+walli/2.+nr*ribspacing;
        //Here use ribs only 10 cm high!
        GeoEllipticalTube(namerib,liscitube/3.,als,bls,walli/2.,zrib - zStartMagVol,18,St,tMaGVol);
      }

      //For Tube nr 5:
      nribs = 2+fTub5length*2./(1.*m) ;
      ribspacing = (fTub5length*2.-nribs*walli)/(nribs-1)+walli;
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        TString namerib = "T5Rib_"; namerib+=nr;
        Double_t zrib= fTub5z-fTub5length+walli/2.+nr*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als,bls,walli/2.,zrib- zStartDecayVol,18,St,tDecayVol);
      }
      //now place LiSc
      for (Int_t nr=1; nr<nribs; nr++) {
        TString namerib = "T5LiSc_"; namerib+=nr;
        Double_t zlength=(ribspacing-walli)/2.;
        Double_t zlisc=fTub5z-fTub5length+walli+zlength+(nr-1)*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als,bls,zlength,zlisc-zStartDecayVol,kMagenta-10,Se,tDecayVol,true);
      }

      //For Tube nr 6:
      nribs = 2+fTub6length*2./(1.*m) ;
      ribspacing = (fTub6length*2.-nribs*walli)/(nribs-1)+walli;
      //now place ribs
      for (Int_t nr=0; nr<nribs; nr++) {
        TString namerib = "T6Rib_"; namerib+=nr;
        Double_t zrib= fTub6z-fTub6length+walli/2.+nr*ribspacing;
        GeoEllipticalTube(namerib,liscitube,als,bls,walli/2.,zrib- zStartDecayVol,18,St,tDecayVol);
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

// Concrete around decay tunnel
      Double_t dZD      =  100*m + fMuonShieldLength;
      TGeoBBox *box3    = new TGeoBBox("box3", 15*m,12.25*m,dZD/2.);
      TGeoBBox *box4    = new TGeoBBox("box4", 10*m, 10*m,dZD/2.);
      TGeoCompositeShape *compRockD = new TGeoCompositeShape("compRockD", "box3-box4");
      TGeoVolume *rockD   = new TGeoVolume("rockD", compRockD, concrete);
      rockD->SetLineColor(11);  // grey
      rockD->SetTransparency(50);
      top->AddNode(rockD, 1, new TGeoTranslation(0, 0, fzOffset + dZD/2.));
// only for fastMuon simulation, otherwise output becomes too big    
      if (fFastMuon){ AddSensitiveVolume(rockD);}

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
