#include "strawtubesPoint.h"

#include <iostream>
#include <math.h>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
strawtubesPoint::strawtubesPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
strawtubesPoint::strawtubesPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
                                   Double_t eLoss)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss)
{
    fT0z=-2390.;                    //!  z-position of veto station
    fT1z=1520.;                     //!  z-position of tracking station 1
    fT2z=1720.;                     //!  z-position of tracking station 2
    fT3z=2160.;                     //!  z-position of tracking station 3 (avoid overlap with magnet)
    fT4z=2380.;                     //!  z-position of tracking station 4 (avoid overlap with ecal)

    fStraw_length=250.;             //!  Length (y) of a straw
    fInner_Straw_diameter=0.94;     //!  Inner Straw diameter
    fOuter_Straw_diameter=0.98;     //!  Outer Straw diameter
    fStraw_pitch=1.76;              //!  Distance (x) between straws in one layer
    fDeltaz_layer12=1.1;            //!  Distance (z) between layer 1&2
    fDeltaz_plane12=2.6;           //!  Distance (z) between plane 1&2
    fOffset_layer12=fStraw_pitch/2; //!  Offset (x) between straws of layer1&2
    fOffset_plane12=fStraw_pitch/4; //!  Offset (x) between straws of plane1&2
    fStraws_per_layer=284;             //!  Number of straws in one layer
    fView_angle=5;                     //!  Stereo angle of layers in a view
    fWire_thickness=0.003;          //!  Thickness of the wire
    fDeltaz_view=10.;               //!  Distance (z) between views
    fVacbox_x=550.;                 //!  x of station vacuum box; x will become y after rotation
    fVacbox_y=300.;                 //!  y of station vacuum box
 //Print(detID);
 //cout<<"x coord of volume "<<StrawX(detID)<< " xtop " << StrawXTop(detID) << " x bot " << StrawXBot(detID) << endl;
 //cout<<"y top coord of volume "<<StrawYTop(detID)<<" y bot coord " << StrawYBot(detID) << endl;
 //cout<<"z coord of volume "<<StrawZ(detID)<<endl;
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
strawtubesPoint::~strawtubesPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void strawtubesPoint::Print(Int_t detID) const
{
  cout << "-I- strawtubesPoint: strawtubes point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

// -----   Public method StrawX    -------------------------------------------
// -----   returns X coordinate of straw -----------------------------------
Double_t strawtubesPoint::StrawX(Int_t detID)
{
  Double_t eps=0.0001;
  Int_t statnb = detID/10000000;
  Int_t vnb = (detID - statnb*10000000)/1000000;
  Int_t pnb = (detID - statnb*10000000 - vnb*1000000)/100000;
  Int_t lnb = (detID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
  Int_t snb = detID - statnb*10000000 - vnb*1000000 - pnb*100000 - lnb*10000 - 1000;
  //cout << "DetID" << detID << " statnb "<<statnb<<" vnb " << vnb << " pnb " << pnb <<" lnb "<< lnb << " snb " << snb << endl;
  Double_t xpos = fStraw_length-fStraw_pitch*snb-8*eps+fStraw_pitch*pnb/4+lnb*fStraw_pitch/2;
  return xpos;
}
// -------------------------------------------------------------------------

// -----   Public method StrawXTop    -------------------------------------------
// -----   returns X Top coordinate of straw -----------------------------------
Double_t strawtubesPoint::StrawXTop(Int_t detID)
{
  Double_t eps=0.0001;
  fStraw_length=250.;             //!  Length (y) of a straw
  fStraw_pitch=1.76;              //!  Distance (x) between straws in one layer
  fView_angle=5;                     //!  Stereo angle of layers in a view
  Int_t angle;
  Int_t statnb = detID/10000000;
  Int_t vnb = (detID - statnb*10000000)/1000000;
  switch (vnb) {
     case 0:
       angle=0; 
       break;
     case 1:
       angle=fView_angle; 
       break;     
     case 2:
       angle=fView_angle; 
       break; 
     case 3:
       angle=0; 
       break; 
     default:
       angle=0;   
   }   
  Double_t pi =  4*atan(1);     
  Double_t sinphi=sin(pi*angle/180.);

  Int_t pnb = (detID - statnb*10000000 - vnb*1000000)/100000;
  Int_t lnb = (detID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
  Int_t snb = detID - statnb*10000000 - vnb*1000000 - pnb*100000 - lnb*10000 - 1000;
  //cout << "DetID" << detID << " statnb "<<statnb<<" vnb " << vnb << " pnb " << pnb <<" lnb "<< lnb << " snb " << snb << endl;
  Double_t xtop = fStraw_length-fStraw_pitch*snb-8*eps+fStraw_pitch*pnb/4+lnb*fStraw_pitch/2;
  xtop = xtop + fStraw_length*sinphi;
  return xtop;
}
// -------------------------------------------------------------------------
// -----   Public method StrawXBot    -------------------------------------------
// -----   returns X Bot coordinate of straw -----------------------------------
Double_t strawtubesPoint::StrawXBot(Int_t detID)
{
  Double_t eps=0.0001;
  Int_t angle;
  fStraw_length=250.;             //!  Length (y) of a straw
  fStraw_pitch=1.76;              //!  Distance (x) between straws in one layer
  fView_angle=5;                     //!  Stereo angle of layers in a view
  Int_t statnb = detID/10000000;
  Int_t vnb = (detID - statnb*10000000)/1000000;
  switch (vnb) {
     case 0:
       angle=0; 
       break;
     case 1:
       angle=fView_angle; 
       break;     
     case 2:
       angle=fView_angle; 
       break; 
     case 3:
       angle=0; 
       break; 
     default:
       angle=0;   
   }   
  Double_t pi =  4*atan(1);     
  Double_t sinphi=sin(pi*angle/180.);

  Int_t pnb = (detID - statnb*10000000 - vnb*1000000)/100000;
  Int_t lnb = (detID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
  Int_t snb = detID - statnb*10000000 - vnb*1000000 - pnb*100000 - lnb*10000 - 1000;
  //cout << "DetID " << detID << " statnb "<<statnb<<" vnb " << vnb << " pnb " << pnb <<" lnb "<< lnb << " snb " << snb << endl;
  Double_t xbot = fStraw_length-fStraw_pitch*snb-8*eps+fStraw_pitch*pnb/4+lnb*fStraw_pitch/2;
  xbot = xbot - fStraw_length*sinphi;
  return xbot;
}
// -------------------------------------------------------------------------

// -----   Public method StrawYTop    -------------------------------------------
// -----   returns Top Y coordinate of straw -----------------------------------
Double_t strawtubesPoint::StrawYTop(Int_t detID)
{
  Double_t eps=0.0001;
  fStraw_length=250.;             //!  Length (y) of a straw
  fView_angle=5;                     //!  Stereo angle of layers in a view
  Int_t statnb = detID/10000000;
  Int_t vnb = (detID - statnb*10000000)/1000000;
  Int_t angle;
  switch (vnb) {
     case 0:
       angle=0; 
       break;
     case 1:
       angle=fView_angle; 
       break;     
     case 2:
       angle=fView_angle; 
       break; 
     case 3:
       angle=0; 
       break; 
     default:
       angle=0;   
   }   
  Double_t pi =  4*atan(1);     
  Double_t cosphi=cos(pi*angle/180.);
  Double_t ypos = fStraw_length*cosphi;
  return ypos;
}
// -------------------------------------------------------------------------

// -----   Public method StrawYBot    -------------------------------------------
// -----   returns Bottom Y coordinate of straw -----------------------------------
Double_t strawtubesPoint::StrawYBot(Int_t detID)
{
  return -StrawYTop(detID);
}
// -------------------------------------------------------------------------

// -----   Public method StrawZ    -------------------------------------------
// -----   returns Z coordinate of straw -----------------------------------
Double_t strawtubesPoint::StrawZ(Int_t detID)
{
  Double_t eps=0.0001;
  fT1z=1520.;                     //!  z-position of tracking station 1
  fT2z=1720.;                     //!  z-position of tracking station 2
  fT3z=2160.;                     //!  z-position of tracking station 3 (avoid overlap with magnet)
  fT4z=2380.;                     //!  z-position of tracking station 4 (avoid overlap with ecal)
  fDeltaz_layer12=1.1;            //!  Distance (z) between layer 1&2
  fDeltaz_plane12=2.6;           //!  Distance (z) between plane 1&2
  fDeltaz_view=10.;               //!  Distance (z) between views
  Int_t statnb = detID/10000000;
  Double_t TStationz;
  switch (statnb) {
     case 0:
       TStationz = fT1z; 
       break;
     case 1:
       TStationz = fT2z; 
       break;
     case 2:
       TStationz = fT3z; 
       break;
     case 3:
       TStationz = fT4z; 
       break;
     default:
       TStationz = fT1z;  
   }                           
  Int_t vnb = (detID - statnb*10000000)/1000000;
  Int_t pnb = (detID - statnb*10000000 - vnb*1000000)/100000;
  Int_t lnb = (detID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
  Int_t snb = detID - statnb*10000000 - vnb*1000000 - pnb*100000 - lnb*10000 - 1000;
  //cout << "DetID " << detID << " Tstationz " << TStationz << " statnb "<<statnb<<" vnb " << vnb << " pnb " << pnb <<" lnb "<< lnb << " snb " << snb << endl;
  Double_t zpos = TStationz+(vnb-3./2.)*fDeltaz_view+(pnb-1./2.)*fDeltaz_plane12+(lnb-1./2.)*fDeltaz_layer12;
  return zpos;
}
// -------------------------------------------------------------------------

ClassImp(strawtubesPoint)

