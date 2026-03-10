// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Timing Detector
// 26/01/2017
// Alexander.Korzenev@cern.ch

#include "TimeDet.h"

#include <iostream>
#include <sstream>

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairLink.h"
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
#include "TimeDetPoint.h"
using std::cout;
using std::endl;

TimeDet::TimeDet()
    : Detector("TimeDet", kTRUE, kTimeDet),
      fzPos(0),
      fxSize(450),
      fySize(650),
      fxBar(168),
      fyBar(6),
      fzBar(1),
      fdzBarCol(2.4),
      fdzBarRow(1.2),
      fNCol(3),
      fNRow(148),
      fxCenter(0),
      fyCenter(0) {
  fNBars = fNCol * fNRow;
  if (fNCol > 1)
    fxOv = (fxBar * fNCol - fxSize) / static_cast<double>(fNCol - 1);
  else
    fxOv = 0;
  if (fNRow > 1)
    fyOv = (fyBar * fNRow - fySize) / static_cast<double>(fNRow - 1);
  else
    fyOv = 0;
}

TimeDet::TimeDet(const char* name, Bool_t active)
    : Detector(name, active, kTimeDet),
      //
      fzPos(0),
      fxSize(450),
      fySize(650),
      fxBar(168),
      fyBar(6),
      fzBar(1),
      fdzBarCol(2.4),
      fdzBarRow(1.2),
      fNCol(3),
      fNRow(148),
      fxCenter(0),
      fyCenter(0) {
  fNBars = fNCol * fNRow;
  if (fNCol > 1)
    fxOv = (fxBar * fNCol - fxSize) / static_cast<double>(fNCol - 1);
  else
    fxOv = 0;
  if (fNRow > 1)
    fyOv = (fyBar * fNRow - fySize) / static_cast<double>(fNRow - 1);
  else
    fyOv = 0;
}

Bool_t TimeDet::ProcessHits(FairVolume* vol) {
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

    // cout << uniqueId << " :(" << xmean << ", " << ymean << ", " << zmean <<
    // "): " << gMC->CurrentVolName() << endl;

    AddHit(fEventID, fTrackID, uniqueId, TVector3(xmean, ymean, zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, fELoss,
           pdgCode, TVector3(Pos.X(), Pos.Y(), Pos.Z()),
           TVector3(Mom.Px(), Mom.Py(), Mom.Pz()));

    // Increment number of veto det points in TParticle
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kTimeDet);
  }

  return kTRUE;
}

void TimeDet::ConstructGeometry() {
  TGeoVolume* top = gGeoManager->GetTopVolume();

  ShipGeo::InitMedium("polyvinyltoluene");
  TGeoMedium* Scint = gGeoManager->GetMedium("polyvinyltoluene");

  ///////////////////////////////////////////////////////

  fDetector = new TGeoVolumeAssembly("Timing Detector");

  TGeoVolume* plate =
      gGeoManager->MakeBox("TimeDet", Scint, fxBar / 2, fyBar / 2, fzBar / 2);
  plate->SetLineColor(kBlue);
  AddSensitiveVolume(plate);

  for (int ib = 0; ib < fNBars; ib++) {
    int irow = 0, icol = 0;
    GetBarRowCol(ib, irow, icol);

    double xbar = 0, ybar = 0, zbar = 0;
    xbar = GetXCol(icol);
    ybar = GetYRow(irow);
    zbar = GetZBar(irow, icol);

    fDetector->AddNode(plate, ib, new TGeoTranslation(xbar, ybar, zbar));

    // printf("%3i  %3i %2i   %8.3f %8.3f %8.3f\n",ib, irow,icol,
    // xbar,ybar,zbar);
  }

  top->AddNode(fDetector, 1, new TGeoTranslation(0, 0, fzPos));

  ///////////////////////////////////////////////////////

  return;
}

void TimeDet::GetBarRowCol(int ib, int& irow, int& icol) const {
  irow = ib / fNCol;
  icol = (ib % fNCol);
  return;
}

double TimeDet::GetXCol(int ic) const {
  ic += 1;
  double x = fxBar * ic - fxOv * (ic - 1) - fxBar / 2;
  return x - fxSize / 2 + fxCenter;
}

double TimeDet::GetYRow(int ir) const {
  ir += 1;
  double y = fyBar * ir - fyOv * (ir - 1) - fyBar / 2;
  return y - fySize / 2 + fyCenter;
}

double TimeDet::GetZBar(int ir, int ic) const {
  double z = (ir % 2) * fdzBarRow + (ic % 2) * fdzBarCol;
  return z;
}
