// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

// Construction of SST tracker stations
// Last update: 15 Aug 2025
// Contact: W.-C. Marty Lee <wei-chieh.lee@desy.de>

#include "strawtubes.h"

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairLogger.h"
#include "FairRootManager.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "TClonesArray.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoTube.h"
#include "TMath.h"
#include "TParticle.h"
#include "TVector3.h"
#include "TVirtualMC.h"
#include "strawtubesPoint.h"

#include <iostream>
#include <sstream>
#include <tuple>
using std::cout;
using std::endl;

strawtubes::strawtubes()
    : FairDetector("strawtubes", kTRUE, kStraw)
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
    : FairDetector("strawtubes", kTRUE, kStraw)
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
    if (dist2Wire > f_inner_straw_diameter / 2){
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
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
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
void strawtubes::SetzPositions(Double_t z1, Double_t z2, Double_t z3, Double_t z4)
{
     f_T1_z = z1;                                               //!  z-position of tracking station 1
     f_T2_z = z2;                                               //!  z-position of tracking station 2
     f_T3_z = z3;                                               //!  z-position of tracking station 3
     f_T4_z = z4;                                               //!  z-position of tracking station 4
}

void strawtubes::SetApertureArea(Double_t width, Double_t height)
{
     f_aperture_width = width;                                  //!  Aperture width (x)
     f_aperture_height = height;                                //!  Aperture height (y)
}

void strawtubes::SetStrawDiameter(Double_t outer_straw_diameter, Double_t wall_thickness)
{
     f_outer_straw_diameter = outer_straw_diameter;             //!  Outer straw diameter
     f_inner_straw_diameter =
       outer_straw_diameter - 2 * wall_thickness;               //!  Inner straw diameter
}

void strawtubes::SetStrawPitch(Double_t straw_pitch, Double_t layer_offset)
{
     f_straw_pitch = straw_pitch;                               //!  Distance (y) between straws in a layer
     f_offset_layer = layer_offset;                             //!  Offset (y) of straws between layers
}

void strawtubes::SetDeltazLayer(Double_t delta_z_layer)
{
     f_delta_z_layer = delta_z_layer;                           //!  Distance (z) between layers
}

void strawtubes::SetStereoAngle(Double_t stereo_angle)
{
     f_view_angle = stereo_angle;                                //!  Stereo view angle
}

void strawtubes::SetWireThickness(Double_t wire_thickness)
{
     f_wire_thickness = wire_thickness;                         //!  Sense wire thickness
}

void strawtubes::SetDeltazView(Double_t delta_z_view)
{
     f_delta_z_view = delta_z_view;                             //!  Distance (z) between stereo views
}

void strawtubes::SetFrameMaterial(TString frame_material)
{
     f_frame_material = frame_material;                         //!  Structure frame material
}

void strawtubes::SetStationEnvelope(Double_t x, Double_t y, Double_t z)
{
     f_station_width = x;                                       //!  Station envelope width (x)
     f_station_height = y;                                      //!  Station envelope height (y)
     f_station_length = z;                                      //!  Station envelope length (z)
}

void strawtubes::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */

    TGeoVolume *top               = gGeoManager->GetTopVolume();
    InitMedium("mylar");
    TGeoMedium *mylar             = gGeoManager->GetMedium("mylar");
    InitMedium("STTmix8020_1bar");
    TGeoMedium *sttmix8020_1bar   = gGeoManager->GetMedium("STTmix8020_1bar");
    InitMedium("tungsten");
    TGeoMedium *tungsten          = gGeoManager->GetMedium("tungsten");
    InitMedium(f_frame_material);
    TGeoMedium *FrameMatPtr       = gGeoManager->GetMedium(f_frame_material);
    InitMedium(fMedium.c_str());
    TGeoMedium* med = gGeoManager->GetMedium(fMedium.c_str());

    gGeoManager->SetVisLevel(4);
    gGeoManager->SetTopVisible();

    // Epsilon to avoid overlapping volumes
    Double_t eps = 0.0001;
    // Straw (half) length
    Double_t straw_length = f_aperture_width + 2. * eps;
    // Width of frame: standard HEA 500 I-beam width
    Double_t frame_width = 49.;
    // Offset due to floor space limitation
    Double_t floor_offset = 14.;

    Double_t rmin, rmax, T_station_z;

    // Arguments of boxes are half-lengths
    TGeoBBox* detbox1 = new TGeoBBox(
        "detbox1", f_aperture_width + frame_width, f_aperture_height + frame_width - floor_offset / 2., f_station_length);
    TGeoBBox* detbox2 = new TGeoBBox(
	"detbox2",
	straw_length + eps,
	f_aperture_height + TMath::Tan(f_view_angle * TMath::Pi() / 180.0) * straw_length * 2 + f_offset_layer / TMath::Cos(f_view_angle * TMath::Pi() / 180.0) + eps,
	f_station_length + eps);
    TGeoTranslation* move_up = new TGeoTranslation("move_up", 0, floor_offset / 2., 0);
    move_up->RegisterYourself();

    // Composite shape to create frame
    TGeoCompositeShape* detcomp1 = new TGeoCompositeShape("detcomp1", "(detbox1:move_up)-detbox2");

    // Volume: straw
    rmin = f_inner_straw_diameter / 2.;
    rmax = f_outer_straw_diameter / 2.;
    // Third argument is half-length of tube
    TGeoTube *straw_tube = new TGeoTube("straw", rmin, rmax, straw_length);
    TGeoVolume *straw = new TGeoVolume("straw", straw_tube, mylar);
    straw->SetLineColor(4);
    straw->SetVisibility(kTRUE);

    // Volume: gas
    rmin = f_wire_thickness / 2. + eps;
    rmax = f_inner_straw_diameter / 2. - eps;
    TGeoTube *gas_tube = new TGeoTube("gas", rmin, rmax, straw_length - 2. * eps);
    TGeoVolume *gas = new TGeoVolume("gas", gas_tube, sttmix8020_1bar);
    gas->SetLineColor(5);
    // Only the gas is sensitive
    AddSensitiveVolume(gas);

    // Volume: wire
    rmin = 0.;
    rmax = f_wire_thickness / 2.;
    TGeoTube *wire_tube = new TGeoTube("wire", rmin, rmax, straw_length - 4. * eps);
    TGeoVolume *wire = new TGeoVolume("wire", wire_tube, tungsten);
    wire->SetLineColor(6);

    // Tracking stations
    // statnb = station number; vnb = view number; lnb = layer number; snb = straw number

    // Station box to contain all components
    TGeoBBox* statbox = new TGeoBBox("statbox", f_station_width, f_station_height - floor_offset / 2., f_station_length);

    f_frame_material.ToLower();

    for (Int_t statnb = 1; statnb < 5; statnb++) {
        // Tracking station loop
        TString nmstation = "Tr";
        std::stringstream ss;
        ss << statnb;
        nmstation = nmstation + ss.str();
        switch (statnb) {
            case 1:
	        T_station_z = f_T1_z;
                break;
            case 2:
                T_station_z = f_T2_z;
                break;
            case 3:
                T_station_z = f_T3_z;
                break;
            case 4:
                T_station_z = f_T4_z;
                break;
            default:
                T_station_z = f_T1_z;
        }

	TGeoVolume* vol = new TGeoVolume(nmstation, statbox, med);
	// z-translate the station to its (absolute) position
	top->AddNode(vol, statnb, new TGeoTranslation(0, floor_offset / 2., T_station_z));

	TGeoVolume* statframe = new TGeoVolume(nmstation + "_frame", detcomp1, FrameMatPtr);
	vol->AddNode(statframe, statnb * 1e6, new TGeoTranslation(0, -floor_offset / 2., 0));
	statframe->SetLineColor(kRed);

        for (Int_t vnb = 0; vnb < 4; vnb++) {
            // View loop
            TString nmview;
            Double_t angle;
	    Double_t stereo_growth;
	    Double_t stereo_pitch;
	    Double_t offset_layer;
	    Int_t straws_per_layer;

            switch (vnb) {
                case 0:
                    angle = 0.;
                    nmview = nmstation + "_y1";
                    break;
                case 1:
                    angle = f_view_angle;
                    nmview = nmstation + "_u";
                    break;
                case 2:
                    angle = -f_view_angle;
                    nmview = nmstation + "_v";
                    break;
                case 3:
                    angle = 0.;
                    nmview = nmstation + "_y2";
                    break;
                default:
                    angle = 0.;
                    nmview = nmstation + "_y1";
            }

	    // Adjustments in the stereo views
	    // stereo_growth: extension of stereo views beyond aperture
	    // stereo_pitch: straw pitch in stereo views
	    // offset_layer: layer offset in stereo views
	    // straws_per_layer: number of straws in one layer with stereo extension
	    // If angle == 0., all numbers return the case of non-stereo views.
	    stereo_growth = TMath::Tan(TMath::Abs(angle) * TMath::Pi() / 180.0) * straw_length;
	    stereo_pitch = f_straw_pitch / TMath::Cos(TMath::Abs(angle) * TMath::Pi() / 180.0);
	    offset_layer = f_offset_layer / TMath::Cos(TMath::Abs(angle) * TMath::Pi() / 180.0);
	    straws_per_layer = std::ceil(2 * (f_aperture_height + stereo_growth) / stereo_pitch);

            for (Int_t lnb = 0; lnb < 2; lnb++) {
                // Layer loop
                TString nmlayer = nmview + "_layer_";
                nmlayer += lnb;
                TGeoBBox* layer = new TGeoBBox(
                    "layer box", straw_length + eps / 4, f_aperture_height + stereo_growth * 2 + offset_layer + eps / 4, f_outer_straw_diameter / 2. + eps / 4);
                TGeoVolume* layerbox = new TGeoVolume(nmlayer, layer, med);

                // The layer box sits in the viewframe.
                // Hence, z-translate the layer w.r.t. the view
                vol->AddNode(layerbox, statnb * 1e6 + vnb * 1e5 + lnb * 1e4, new TGeoTranslation(0, -floor_offset / 2., (vnb - 3. / 2.) * f_delta_z_view + (lnb - 1. / 2.) * f_delta_z_layer));

                TGeoRotation r6s;
                TGeoTranslation t6s;
                for (Int_t snb = 1; snb <= straws_per_layer; snb++) {
                    // Straw loop
		    // y-translate the straw to its position
		    t6s.SetTranslation(0, f_aperture_height + stereo_growth - (snb - 1. / 2.) * stereo_pitch + lnb * offset_layer, 0);
		    // Rotate the straw with stereo angle
                    r6s.SetAngles(90 + angle, 90, 0);
                    TGeoCombiTrans c6s(t6s, r6s);
                    TGeoHMatrix* h6s = new TGeoHMatrix(c6s);
                    layerbox->AddNode(straw, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 1e3 + snb, h6s);
                    layerbox->AddNode(gas, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 2e3 + snb, h6s);
                    layerbox->AddNode(wire, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 3e3 + snb, h6s);
                    // End of straw loop
                }

		if (lnb == 1) {
		   // Add one more straw at the bottom of the second layer to cover aperture entirely
		   t6s.SetTranslation(0, f_aperture_height + stereo_growth - (straws_per_layer - 1. / 2.) * stereo_pitch - lnb * offset_layer, 0);
                   r6s.SetAngles(90 + angle, 90, 0);
                   TGeoCombiTrans c6s(t6s, r6s);
                   TGeoHMatrix* h6s = new TGeoHMatrix(c6s);
                   layerbox->AddNode(straw, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 1e3 + straws_per_layer + 1, h6s);
                   layerbox->AddNode(gas, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 2e3 + straws_per_layer + 1, h6s);
                   layerbox->AddNode(wire, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 3e3 + straws_per_layer + 1, h6s);
		}
                // End of layer loop
            }
            // End of view loop
        }
        // End of tracking station loop
    }
}
// -----   Public method StrawDecode    -------------------------------------------
// -----   returns station, view, layer, straw number in a tuple -----------------------------------
std::tuple<Int_t, Int_t, Int_t, Int_t> strawtubes::StrawDecode(Int_t detID)
{
    Int_t statnb, vnb, lnb, snb;
    statnb = detID / 1e6;
    vnb = (detID - statnb * 1e6) / 1e5;
    lnb = (detID - statnb * 1e6 - vnb * 1e5) / 1e4;
    snb = detID - statnb * 1e6 - vnb * 1e5 - lnb * 1e4 - 2e3;

    if (statnb < 1 || statnb > 4 || vnb < 0 || vnb > 3 || lnb < 0 || lnb > 1 || snb < 1 || snb > 317) {
        LOG(warning) << "Invalid strawtubes detID:";
        LOG(warning) << detID << " -> station: " << statnb << ", view: " << vnb << ", layer: " << lnb
                     << ", straw: " << snb;
        LOG(warning) << "strawtubes detID is 7-digit!";
        return std::make_tuple(0, -1, -1, 0);
    } else {
        return std::make_tuple(statnb, vnb, lnb, snb);
    }
}
// -----   Public method StrawEndPoints    -------------------------------------------
// -----   returns top (left) and bottom (right) coordinates of straw -----------------------------------
void strawtubes::StrawEndPoints(Int_t fDetectorID, TVector3 &vbot, TVector3 &vtop)
// method to get end points from TGeoNavigator
{
    const auto [statnb, vnb, lnb, snb] = StrawDecode(fDetectorID);
    TString stat = "Tr"; stat += statnb; stat += "_"; stat += statnb;
    TString view;
    switch (vnb) {
	      case 0:
	        view = "_y1";
	        break;
	      case 1:
	      	view = "_u";
	        break;
	      case 2:
	        view = "_v";
	        break;
	      case 3:
	        view = "_y2";
	        break;
	      default:
	        view = "_y1";
    }
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    TString prefix = "Tr";
    prefix += statnb;
    prefix += view;
    prefix += "_";
    TString layer = prefix + "layer_";
    layer += lnb;
    layer += "_";
    layer += statnb;
    layer += vnb;
    layer += lnb;
    layer += "0000";
    TString wire = "wire_";
    wire += fDetectorID + 1e3;
    TString path = "/";
    path += stat;
    path += "/";
    path += layer;
    path += "/";
    path += wire;
    Bool_t rc = nav->cd(path);
    if (!rc) {
        LOG(warning) << "strawtubes::StrawDecode, TGeoNavigator failed" << path;
        return;
    }
    TGeoNode* W = nav->GetCurrentNode();
    TGeoTube* S = dynamic_cast<TGeoTube*>(W->GetVolume()->GetShape());
    Double_t top[3] = {0, 0, S->GetDZ()};
    Double_t bot[3] = {0, 0, -S->GetDZ()};
    Double_t Gtop[3], Gbot[3];
    nav->LocalToMaster(top, Gtop); nav->LocalToMaster(bot, Gbot);
    vtop.SetXYZ(Gtop[0], Gtop[1], Gtop[2]);
    vbot.SetXYZ(Gbot[0], Gbot[1], Gbot[2]);
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
