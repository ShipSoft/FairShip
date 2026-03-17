// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// RPC Timing Detector
// 17/12/2019
// celso.franco@cern.ch

#include "UpstreamTagger.h"

#include <ROOT/TSeq.hxx>
#include <iostream>
#include <sstream>

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairRootManager.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
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
#include "UpstreamTaggerHit.h"
#include "UpstreamTaggerPoint.h"
using ROOT::TSeq;
using ShipUnit::cm;
using ShipUnit::m;
using std::cout;
using std::endl;

UpstreamTagger::UpstreamTagger()
    : Detector("UpstreamTagger", kTRUE, kUpstreamTagger),
      det_zPos(0),
      UpstreamTagger_fulldet(0),
      scoringPlaneUBText(0) {}

UpstreamTagger::UpstreamTagger(const char* name, Bool_t active)
    : Detector(name, active, kUpstreamTagger),
      det_zPos(0),
      UpstreamTagger_fulldet(0),
      scoringPlaneUBText(0) {}

Bool_t UpstreamTagger::ProcessHits(FairVolume* vol) {
  /** This method is called from the MC stepping */
  // Set parameters at entrance of volume. Reset ELoss.
  if (gMC->IsTrackEntering()) {
    fELoss = 0.;
    fTime = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
  }

  // Sum energy loss for all steps in the active volume
  fELoss += gMC->Edep();

  // Create vetoPoint at exit of active volume
  if (gMC->IsTrackExiting() || gMC->IsTrackStop() ||
      gMC->IsTrackDisappeared()) {
    if (fELoss == 0.) {
      return kFALSE;
    }

    fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
    fEventID = gMC->CurrentEvent();
    Int_t uniqueId;
    gMC->CurrentVolID(uniqueId);
    if (uniqueId > 1000000)  // Solid scintillator case
    {
      Int_t vcpy;
      gMC->CurrentVolOffID(1, vcpy);
      if (vcpy == 5) uniqueId += 4;  // Copy of half
    }

    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X() + Pos.X()) / 2.;
    Double_t ymean = (fPos.Y() + Pos.Y()) / 2.;
    Double_t zmean = (fPos.Z() + Pos.Z()) / 2.;

    AddHit(fEventID, fTrackID, uniqueId, TVector3(xmean, ymean, zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, fELoss,
           pdgCode, TVector3(Pos.X(), Pos.Y(), Pos.Z()),
           TVector3(Mom.Px(), Mom.Py(), Mom.Pz()));

    // Increment number of veto det points in TParticle
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kUpstreamTagger);
  }

  return kTRUE;
}

void UpstreamTagger::ConstructGeometry() {
  TGeoVolume* top = gGeoManager->GetTopVolume();

  //////////////////////////////////////////////////////

  ///////////////////////////////////////////////////////

  ///////////////////////////////////////////////////////

  ShipGeo::InitMedium("vacuum");
  TGeoMedium* Vacuum_box = gGeoManager->GetMedium("vacuum");
  ///////////////////////////////////////////////////////////////////

  // Adding UBT Extension
  if (!Vacuum_box) {
    Fatal("ConstructGeometry", "Medium 'vacuum' not found.");
  }

  UpstreamTagger_fulldet =
      gGeoManager->MakeBox("Upstream_Tagger", Vacuum_box, xbox_fulldet / 2.0,
                           ybox_fulldet / 2.0, zbox_fulldet / 2.0);
  UpstreamTagger_fulldet->SetLineColor(kGreen);

  top->AddNode(UpstreamTagger_fulldet, 1,
               new TGeoTranslation(0.0, 0.0, det_zPos));
  AddSensitiveVolume(UpstreamTagger_fulldet);
  cout << " Z Position (Upstream Tagger1) " << det_zPos << endl;
  //////////////////////////////////////////////////////////////////

  return;
}
