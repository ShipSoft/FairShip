// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "exitHadronAbsorber.h"

#include <cstddef>
#include <iostream>

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairLogger.h"
#include "FairRootManager.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "TArrayI.h"
#include "TDatabasePDG.h"
#include "TGeoBBox.h"
#include "TGeoBoolNode.h"
#include "TGeoEltu.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TLorentzVector.h"
#include "TMCProcess.h"
#include "TParticle.h"
#include "TROOT.h"
#include "TVirtualMC.h"
#include "vetoPoint.h"

using std::cout;
using std::endl;

constexpr Double_t cm = 1;         // cm
constexpr Double_t m = 100 * cm;   //  m
constexpr Double_t mm = 0.1 * cm;  //  mm

namespace {
// ShipStack::PushTrack multiplies the weight of a pushed track by that of the
// track it names as parent, and leaves it alone for a primary. A clone that
// should end up with weight w is therefore pushed with w divided by this.
Double_t PushedWeightScale(Int_t parentId) {
  if (parentId < 0) {
    return 1.;
  }
  auto* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
  TParticle* parent = stack->GetParticle(parentId);
  if (!parent || parent->GetWeight() <= 0.) {
    return 1.;
  }
  return parent->GetWeight();
}
}  // namespace

Int_t exitHadronAbsorber::fgCarrierTrackID = exitHadronAbsorber::kNoCarrier;
std::set<Int_t> exitHadronAbsorber::fgShadowTracks;

exitHadronAbsorber::exitHadronAbsorber(const char* Name, Bool_t Active)
    : Detector(Name, Active, kVETO),
      fOnlyMuons(kFALSE),
      fSkipNeutrinos(kFALSE),
      fVetoName("veto"),
      fzPos(3E8),
      withNtuple(kFALSE),
      fCylindricalPlane(kFALSE),
      fUseCaveCoordinates(kFALSE),
      fNsplits(0),
      fIntermediateNsplits(2) {}

exitHadronAbsorber::exitHadronAbsorber()
    : Detector("exitHadronAbsorber", kTRUE, kVETO),
      fUniqueID(-1),
      fOnlyMuons(kFALSE),
      fSkipNeutrinos(kFALSE),
      fVetoName("veto"),
      fzPos(3E8),
      withNtuple(kFALSE),
      fCylindricalPlane(kFALSE),
      fUseCaveCoordinates(kFALSE),
      fNsplits(0),
      fIntermediateNsplits(2) {}

void exitHadronAbsorber::SetMaxSplitBuffer(Int_t n) {
  // Guard the conversion: a negative value would become a huge std::size_t and
  // silently disable the safety valve.
  if (n < 1) {
    LOG(error) << "exitHadronAbsorber: max split buffer must be >= 1, ignoring "
               << n;
    return;
  }
  fMaxSplitBuffer = static_cast<std::size_t>(n);
}

void exitHadronAbsorber::SetMaxEventSize(Int_t n) {
  if (n < 1) {
    LOG(error) << "exitHadronAbsorber: max event size must be >= 1, ignoring "
               << n;
    return;
  }
  fMaxEventSize = static_cast<std::size_t>(n);
}

Bool_t exitHadronAbsorber::ProcessHits(FairVolume* vol) {
  /** This method is called from the MC stepping */
  TString volName = gMC->CurrentVolName();

  // Only this detector's own plane: with per-step splitting the volumes
  // registered below the target include other exitHadronAbsorber planes, whose
  // names share the prefix.
  if (volName == fPlaneVolName) {
    if (gMC->IsTrackEntering()) {
      fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
      fEventID = gMC->CurrentEvent();
      TParticle* p = gMC->GetStack()->GetCurrentTrack();
      fUniqueID = p->GetUniqueID();
      Int_t pdgCode = p->GetPdgCode();
      Int_t motherId = p->GetFirstMother();
      gMC->TrackMomentum(fMom);
      if (!fOnlyMuons || TMath::Abs(pdgCode) == 13) {
        fTime = gMC->TrackTime() * 1.0e09;
        fLength = gMC->TrackLength();
        gMC->TrackPosition(fPos);
        if (((fMom.E() - fMom.M()) > EMax) &&
            (fDecayedParentIDs.count(motherId) == 0) &&
            (fgShadowTracks.count(fTrackID) == 0)) {
          AddHit(fEventID, fTrackID, 111,
                 TVector3(fPos.X(), fPos.Y(), fPos.Z()),
                 TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, 0,
                 pdgCode, TVector3(p->Vx(), p->Vy(), p->Vz()),
                 TVector3(p->Px(), p->Py(), p->Pz()));
          auto* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
          stack->AddPoint(kVETO);
        }
      }
    }

    if ((!fCylindricalPlane) && fzPos > 1E8) {
      gMC->StopTrack();
    }
  }

  // Both counts have to be positive: PostTrack() only terminates the ledger,
  // handing what is left of it to the endpoint clones, when fNsplits > 0.
  // run_fixedTarget.py pairs the two options for the same reason.
  if (fNsplits > 0 && fIntermediateNsplits > 0 && (!fSplitOnce)) {
    Int_t currentTrackId = gMC->GetStack()->GetCurrentTrackNumber();

    if (fCloneTracks.count(currentTrackId) > 0 ||
        fgShadowTracks.count(currentTrackId) > 0) {
      return kTRUE;
    }

    Int_t track_pid = gMC->TrackPid();
    bool kaon_or_pion =
        (TMath::Abs(track_pid) == 211 || TMath::Abs(track_pid) == 321);

    if (kaon_or_pion) {
      TParticle* part = gMC->GetStack()->GetCurrentTrack();
      if (!part) return kTRUE;

      Double_t delta_s = gMC->TrackStep();

      if (delta_s > 0) {
        TLorentzVector pos, mom;
        gMC->TrackPosition(pos);
        gMC->TrackMomentum(mom);

        Double_t mass = gMC->TrackMass();
        Double_t tau = gMC->ParticleLifeTime(track_pid);  // in nanoseconds
        Double_t c_tau = tau * 29.9792458;                // in cm/ns

        Double_t instantP = mom.P();

        Double_t lambda_decay = (instantP / mass) * c_tau;
        Double_t P_decay = 1.0 - TMath::Exp(-delta_s / lambda_decay);
        if ((P_decay > 0.0) && ((mom.E() - mom.M()) > EMax)) {
          double polX = 0, polY = 0, polZ = 0;
          TVector3 polVector;
          part->GetPolarisation(polVector);
          polX = polVector.X();
          polY = polVector.Y();
          polZ = polVector.Z();
          Int_t trueParentId = part->GetFirstMother();

          // Reserve room for the fNsplits endpoint clones PostTrack() appends
          // when the parent finally decays, so the buffer never exceeds
          // fMaxSplitBuffer. All terms are on the left to keep the unsigned
          // arithmetic from wrapping.
          const std::size_t secondaryBufferSize = fSecondaryBuffer.size();
          const std::size_t event_size = gMC->GetStack()->GetNtrack();

          const std::size_t pending =
              secondaryBufferSize +
              static_cast<std::size_t>(fIntermediateNsplits) +
              static_cast<std::size_t>(fNsplits);
          const bool bufferFull = pending > fMaxSplitBuffer;
          const std::size_t projected_size =
              event_size + pending * kShowerSafetyFactor;
          const bool eventFull = projected_size > fMaxEventSize;
          if (bufferFull || eventFull) {
            // Skip the split for this step instead of truncating the buffer.
            // The track weight is the ledger: leaving it untouched
            // means the weight we did not split off is still carried by the
            // track, and reaches the natural-decay clones in PostTrack() if
            // the track ends in a decay. The total weight the track
            // contributes is unchanged, only the statistical boost is reduced.
            if (bufferFull && !fSplitBufferLimitWarned) {
              LOG(warning) << "exitHadronAbsorber: intermediate split buffer "
                              "reached "
                           << secondaryBufferSize
                           << " entries; skipping further per-step splitting "
                              "(reported once per event). Consider lowering "
                              "--intermediate-kaon-pion-splits or raising "
                              "--max-split-buffer.";
              fSplitBufferLimitWarned = kTRUE;
            }
            if (eventFull && !fEventSizeLimitWarned) {
              LOG(warning) << "exitHadronAbsorber: event size reached "
                           << event_size << " entries, projected size "
                           << projected_size
                           << " with the pending split clones; skipping "
                              "further per-step splitting (reported once per "
                              "event). Consider lowering "
                              "--intermediate-kaon-pion-splits or raising "
                              "--max-event-size.";
              fEventSizeLimitWarned = kTRUE;
            }
            return kTRUE;
          }

          // The track's own weight is the ledger: it starts at whatever the
          // track was pushed with and loses the decay branch at every split.
          // The clones get exactly what the track loses, so track + clones
          // keep the weight the track started with at every step, whatever
          // that weight is, even if it differs from that of the track
          // ShipStack scales the clones by (see PushedWeightScale). Lowering
          // the track's weight also keeps everything it goes on to do in
          // step: its hit at the sensitive plane, and the secondaries it
          // makes if it ends by interacting rather than decaying. Geant4
          // pushes a secondary onto the VMC stack when that secondary starts
          // tracking, which is after the parent is done, so the secondaries
          // pick this up on their own. This relies on
          // /mcTracking/saveSecondariesInStep staying off (see
          // gconfig/g4config.in); turning it on pushes secondaries during the
          // step that makes them. A side effect is that secondaries made
          // mid-track by processes that do not end it (delta rays, elastic
          // recoils) get the parent's final weight, not its weight at the
          // step that made them. That is negligible for the muon rate, but do
          // not rely on their weights.
          const Double_t trackWeight = part->GetWeight();
          const Double_t cloneWeight = trackWeight * P_decay /
                                       fIntermediateNsplits /
                                       PushedWeightScale(trueParentId);
          for (int i = 0; i < fIntermediateNsplits; ++i) {
            TrackBuffer clone;
            clone.pdg = track_pid;
            clone.px = mom.Px();
            clone.py = mom.Py();
            clone.pz = mom.Pz();
            clone.e = mom.E();
            clone.x = pos.X();
            clone.y = pos.Y();
            clone.z = pos.Z();
            clone.t = pos.T();
            clone.polx = polX;
            clone.poly = polY;
            clone.polz = polZ;
            clone.weight = cloneWeight;
            clone.parentID = trueParentId;
            fSecondaryBuffer.push_back(clone);
          }
          part->SetWeight(trackWeight * (1.0 - P_decay));
          fSplitDecays++;
          fClonesBuffered += fIntermediateNsplits;
          RequestCloneCarrier();
        }
      }
    }
  }
  return kTRUE;
}

void exitHadronAbsorber::Initialize() {
  SHiP::Detector<vetoPoint>::Initialize();
  // PostTrack() buffers fNsplits endpoint clones for every splitting decay in
  // both modes, without consulting the cap, so a cap below fNsplits breaks the
  // hard bound. With per-step splitting it also makes the ProcessHits()
  // reservation permanently unsatisfiable, disabling per-step splitting.
  if (fNsplits > 0 && static_cast<std::size_t>(fNsplits) > fMaxSplitBuffer) {
    LOG(fatal) << "exitHadronAbsorber: max split buffer (" << fMaxSplitBuffer
               << ") must be at least the endpoint split count (" << fNsplits
               << ")";
  }
  TSeqCollection* fileList = gROOT->GetListOfFiles();
  fout = dynamic_cast<TFile*>(fileList->At(0));
  // book hists for Genie neutrino momentum distribution
  // add also leptons, and photon
  // add pi0 111 eta 221 eta' 331  omega 223 for DM production
  TDatabasePDG* PDG = TDatabasePDG::Instance();
  for (Int_t idnu = 11; idnu < 26; idnu += 1) {
    // nu or anti-nu
    for (Int_t idadd = -1; idadd < 3; idadd += 2) {
      Int_t idw = idnu;
      if (idnu == 18) {
        idw = 22;
      }
      if (idnu == 19) {
        idw = 111;
      }
      if (idnu == 20) {
        idw = 221;
      }
      if (idnu == 21) {
        idw = 223;
      }
      if (idnu == 22) {
        idw = 331;
      }
      if (idnu == 23) {
        idw = 211;
      }
      if (idnu == 24) {
        idw = 321;
      }
      if (idnu == 25) {
        idw = 2212;
      }
      Int_t idhnu = 10000 + idw;
      if (idadd == -1) {
        if (idnu > 17) {
          continue;
        }
        idhnu += 10000;
        idw = -idnu;
      }
      TString name = PDG->GetParticle(idw)->GetName();
      TString title = name;
      title += " momentum (GeV)";
      TString key = fVetoName;
      key += idhnu;
      [[maybe_unused]] TH1D* Hidhnu = new TH1D(key, title, 400, 0., 400.);
      title = name;
      title += "  log10-p vs log10-pt";
      key = fVetoName;
      key += idhnu + 1000;
      [[maybe_unused]] TH2D* Hidhnu100 =
          new TH2D(key, title, 100, -0.3, 1.7, 100, -2., 0.5);
      title = name;
      title += "  log10-p vs log10-pt";
      key = fVetoName;
      key += idhnu + 2000;
      [[maybe_unused]] TH2D* Hidhnu200 =
          new TH2D(key, title, 25, -0.3, 1.7, 100, -2., 0.5);
    }
  }
  if (withNtuple) {
    fNtuple = new TNtuple("4DP", "4DP", "id:px:py:pz:x:y:z");
  }
}

void exitHadronAbsorber::BeginEvent() {
  fgCarrierTrackID = kNoCarrier;
  fgShadowTracks.clear();
  fCloneTracks.clear();
  fDecayedParentIDs.clear();
  fSplitBufferLimitWarned = kFALSE;
  fEventSizeLimitWarned = kFALSE;
}

void exitHadronAbsorber::FinishEvent() {
  // Checked here rather than at the start of the next event so that the last
  // event of a run is covered too.
  DiscardBufferedClones();
}

void exitHadronAbsorber::DiscardBufferedClones() {
  if (fSecondaryBuffer.empty()) {
    return;
  }
  // No track carried these clones to the stack popper before the event
  // ended, so their weight never made it into the simulation.
  Double_t lostWeight = 0;
  for (const auto& trk : fSecondaryBuffer) {
    lostWeight += trk.weight;
  }
  fLostBufferEvents++;
  fLostCloneTracks += static_cast<Int_t>(fSecondaryBuffer.size());
  fLostCloneWeight += lostWeight;
  LOG(warning) << "exitHadronAbsorber: discarding " << fSecondaryBuffer.size()
               << " buffered split clones (summed weight " << lostWeight
               << ") which no track handed to the stack popper";
  fSecondaryBuffer.clear();
}

void exitHadronAbsorber::PostTrack() {
  Int_t currentTrackId = gMC->GetStack()->GetCurrentTrackNumber();

  // A shadow must not split either: its clones would be exempt from the cut.
  if (fCloneTracks.count(currentTrackId) > 0 ||
      fgShadowTracks.count(currentTrackId) > 0) {
    return;
  }

  Int_t track_pid = gMC->TrackPid();
  bool kaon_or_pion =
      (TMath::Abs(track_pid) == 211 || TMath::Abs(track_pid) == 321);

  if (fNsplits > 0 && kaon_or_pion) {
    bool isNaturalDecay = false;
    TArrayI processes;
    gMC->StepProcesses(processes);
    for (int i = 0; i < processes.GetSize(); i++) {
      if (processes[i] == kPDecay) {
        isNaturalDecay = true;
        break;
      }
    }

    TParticle* part = gMC->GetStack()->GetCurrentTrack();
    if (!part) return;

    TLorentzVector finalPos, finalMom;
    gMC->TrackPosition(finalPos);
    gMC->TrackMomentum(finalMom);

    double polX = 0, polY = 0, polZ = 0;
    TVector3 polVector;
    part->GetPolarisation(polVector);
    polX = polVector.X();
    polY = polVector.Y();
    polZ = polVector.Z();
    Int_t trueParentId = part->GetFirstMother();

    // A track that decays hands all of its remaining weight to the endpoint
    // clones. With per-step splitting its weight has already been lowered by
    // every split along the way.
    if (isNaturalDecay) {
      Double_t finalEndpointWeight =
          part->GetWeight() / fNsplits / PushedWeightScale(trueParentId);
      for (int i = 0; i < fNsplits; ++i) {
        TrackBuffer clone;
        clone.pdg = track_pid;
        clone.px = finalMom.Px();
        clone.py = finalMom.Py();
        clone.pz = finalMom.Pz();
        clone.e = finalMom.E();
        clone.x = finalPos.X();
        clone.y = finalPos.Y();
        clone.z = finalPos.Z();
        clone.t = finalPos.T();
        clone.polx = polX;
        clone.poly = polY;
        clone.polz = polZ;
        clone.weight = finalEndpointWeight;
        clone.parentID = trueParentId;
        fSecondaryBuffer.push_back(clone);
      }
      fDecayedParentIDs.insert(currentTrackId);
      fSplitDecays++;
      fClonesBuffered += fNsplits;
      RequestCloneCarrier();
    }

    // A track that ends any other way keeps the remaining weight itself, so
    // there is nothing to hand on. Geant4 never gives us a track that is
    // still going: G4TrackingManager steps while the status is fAlive or
    // fStopButAlive, TG4TrackingAction::PostUserTrackingAction skips
    // PostTrack for fSuspend, and IsTrackStop() covers every status that is
    // left. StopTrack() stays because it is the one call here that can still
    // matter for a status other than fStopAndKill.
    gMC->StopTrack();
  }
}

void exitHadronAbsorber::PreTrack() {
  // Invariant for this whole method: the clone buffer may only be handed to a
  // carrier that is guaranteed to step. TG4StackPopper converts pushed tracks
  // into Geant4 secondaries from PostStepDoIt only, and its Reset() at the
  // start of the next track writes off everything still pending, so a carrier
  // stopped before its first step swallows the entire set. Every reason to stop
  // this track is therefore settled before the flush at the end.
  gMC->TrackMomentum(fMom);
  TParticle* p = gMC->GetStack()->GetCurrentTrack();
  Int_t currentID = gMC->GetStack()->GetCurrentTrackNumber();
  Bool_t isClone = (fCloneTracks.find(currentID) != fCloneTracks.end());

  // Claim the carrier for the clones buffered by the last splitting decay. A
  // decay always puts its daughters on the stack, so some track always follows
  // it; only the cuts below can strand the buffer until the event ends.
  Bool_t isCarrier =
      (fgCarrierTrackID == kCarrierRequested || fgCarrierTrackID == currentID);
  if (fgCarrierTrackID == kCarrierRequested) {
    fgCarrierTrackID = currentID;
  }

  Int_t pdgCode = p->GetPdgCode();
  Int_t idabs = TMath::Abs(pdgCode);
  Bool_t belowCut = (fMom.E() - fMom.M()) < EMax;
  Bool_t skippedNeutrino =
      fSkipNeutrinos && (idabs == 12 || idabs == 14 || idabs == 16);

  // A shadow is a track that an unsplit run would never have transported: a
  // carrier that is only exempt from a stop so that it steps, or a descendant
  // of a shadow. A shadow's secondaries can still pass the cut, because a
  // decay turns rest mass into kinetic energy (a slow pi0 can give a photon
  // above it), so they are stopped too, and no plane scores a shadow. Clones
  // are never shadows: their parent is the split track, not the carrier.
  Bool_t inheritedShadow =
      !isClone && fgShadowTracks.count(p->GetFirstMother()) > 0;
  Bool_t carrierShadow = isCarrier && !isClone && (belowCut || skippedNeutrino);

  if (!isClone && !isCarrier && (belowCut || inheritedShadow)) {
    // Do NOT flush the clone buffer into this track: it is stopped before its
    // first step, so the stack popper would never run for it and the pending
    // clones would be silently discarded at the next track's popper reset.
    // The designated carrier is exempt so that it does step, and becomes a
    // shadow instead.
    //
    // Clones are exempt from the cut. They are a bookkeeping device that has
    // to decay immediately (ForceDecayTime(0)) so that the decay can be
    // re-sampled, and their parent already passed the cut at the start of its
    // own track. Applying the cut again at the decay point would drop decay
    // products which an unsplit run keeps, because there the cut acts on the
    // (possibly much harder) decay muon rather than on the parent. The decay
    // products of the clones are cut as usual.
    gMC->StopTrack();
    return;
  }

  if (inheritedShadow || carrierShadow) {
    fgShadowTracks.insert(currentID);
  }

  // A shadow only has to step so that the stack popper hands the clones over.
  // An unsplit run would have stopped it above, so it must not reach the
  // histograms or the ntuple. The exception is a neutrino above the cut, which
  // an unsplit run records before stopping it.
  const Bool_t recordStatistics =
      !(inheritedShadow || (carrierShadow && belowCut));

  // record statistics for neutrinos, electrons and photons
  // add pi0 111 eta 221 eta' 331  omega 223
  if (recordStatistics && (idabs < 18 || idabs == 22 || idabs == 111 ||
                           idabs == 221 || idabs == 223 || idabs == 331 ||
                           idabs == 211 || idabs == 321 || idabs == 2212)) {
    Double_t wspill = p->GetWeight();
    Int_t idhnu = idabs + 10000;
    if (pdgCode < 0) {
      idhnu += 10000;
    }
    Double_t l10ptot =
        TMath::Min(TMath::Max(TMath::Log10(fMom.P()), -0.3), 1.69999);
    Double_t l10pt =
        TMath::Min(TMath::Max(TMath::Log10(fMom.Pt()), -2.), 0.4999);
    TString key = fVetoName;
    key += idhnu;
    TH1D* h1 = dynamic_cast<TH1D*>(fout->Get(key));
    if (h1) {
      h1->Fill(fMom.P(), wspill);
    }
    key = fVetoName;
    key += idhnu + 1000;
    TH2D* h2 = dynamic_cast<TH2D*>(fout->Get(key));
    if (h2) {
      h2->Fill(l10ptot, l10pt, wspill);
    }
    key = fVetoName;
    key += idhnu + 2000;
    h2 = dynamic_cast<TH2D*>(fout->Get(key));
    if (h2) {
      h2->Fill(l10ptot, l10pt, wspill);
    }
    if (withNtuple) {
      fNtuple->Fill(pdgCode, fMom.Px(), fMom.Py(), fMom.Pz(), fPos.X(),
                    fPos.Y(), fPos.Z());
    }
    if (skippedNeutrino && !isCarrier) {
      // The statistics above are still recorded, but the track is stopped
      // before its first step, so it must not receive the clone buffer.
      gMC->StopTrack();
      return;
    }
  }

  // A module whose PreTrack() ran before ours may already have stopped the
  // track: FairMCApplication calls the detectors in registration order, and
  // run_fixedTarget.py registers the other exitHadronAbsorber planes ahead of
  // the one that owns the split buffer. A module registered after this one is
  // not covered: if it stops the track, the clones flushed below are lost.
  if (!gMC->IsTrackAlive()) {
    return;
  }

  if (!fSecondaryBuffer.empty()) {
    auto* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    Int_t ntr;
    for (const auto& trk : fSecondaryBuffer) {
      stack->PushTrack(1, trk.parentID, trk.pdg, trk.px, trk.py, trk.pz, trk.e,
                       trk.x, trk.y, trk.z, trk.t, trk.polx, trk.poly, trk.polz,
                       kPNoProcess, ntr, trk.weight, 999);
      fCloneTracks.insert(ntr);
    }
    // Clear the buffer so we don't duplicate them for the next track
    fSecondaryBuffer.clear();
  }

  if (isClone) {
    //  Force the decay time to 0
    gMC->ForceDecayTime(0);
  }
}

void exitHadronAbsorber::FinishRun() {
  // BeginEvent only sees the buffer of the previous event, so the last event
  // of the run has to be checked here.
  DiscardBufferedClones();
  if (fNsplits > 0) {
    LOG(info) << "exitHadronAbsorber: split " << fSplitDecays
              << " times, creating " << fClonesBuffered << " clones";
    if (fLostBufferEvents > 0) {
      LOG(warning) << "exitHadronAbsorber: " << fLostBufferEvents
                   << " event(s) ended with buffered split clones, losing "
                   << fLostCloneTracks << " clones of summed weight "
                   << fLostCloneWeight;
    } else {
      LOG(info) << "exitHadronAbsorber: every buffered split clone was tracked";
    }
  }
  for (Int_t idnu = 11; idnu < 23; idnu += 1) {
    // nu or anti-nu
    for (Int_t idadd = -1; idadd < 3; idadd += 2) {
      Int_t idw = idnu;
      if (idnu == 18) {
        idw = 22;
      }
      if (idnu == 19) {
        idw = 111;
      }
      if (idnu == 20) {
        idw = 221;
      }
      if (idnu == 21) {
        idw = 223;
      }
      if (idnu == 22) {
        idw = 331;
      }
      Int_t idhnu = 10000 + idw;
      if (idadd == -1) {
        if (idnu > 17) {
          continue;
        }
        idhnu += 10000;
        idw = -idnu;
      }
      TString key = fVetoName;
      key += idhnu;
      TSeqCollection* fileList = gROOT->GetListOfFiles();
      dynamic_cast<TFile*>(fileList->At(0))->cd();
      TH1D* Hidhnu = dynamic_cast<TH1D*>(fout->Get(key));
      Hidhnu->Write();
      key = fVetoName;
      key += idhnu + 1000;
      TH2D* Hidhnu100 = dynamic_cast<TH2D*>(fout->Get(key));
      Hidhnu100->Write();
      key = fVetoName;
      key += idhnu + 2000;
      TH2D* Hidhnu200 = dynamic_cast<TH2D*>(fout->Get(key));
      Hidhnu200->Write();
    }
  }
  if (withNtuple) {
    fNtuple->Write();
  }
}

void RegisterDaughtersRecursively(TGeoVolume* volume,
                                  exitHadronAbsorber* detector) {
  if (!volume) return;
  Int_t nDaughters = volume->GetNdaughters();
  for (Int_t i = 0; i < nDaughters; ++i) {
    TGeoNode* daughterNode = volume->GetNode(i);
    if (daughterNode) {
      TGeoVolume* daughterVol = daughterNode->GetVolume();
      if (daughterVol) {
        // register daughter volume
        detector->AddSensitiveVolume(daughterVol);
        LOG(info) << "[exitHadronAbsorber] Registered subvolume: "
                  << daughterVol->GetName();
        // call function recursively
        RegisterDaughtersRecursively(daughterVol, detector);
      }
    }
  }
}

void exitHadronAbsorber::ConstructGeometry() {
  static FairGeoLoader* geoLoad = FairGeoLoader::Instance();
  static FairGeoInterface* geoFace = geoLoad->getGeoInterface();
  static FairGeoMedia* media = geoFace->getMedia();
  static FairGeoBuilder* geoBuild = geoLoad->getGeoBuilder();

  FairGeoMedium* ShipMedium = media->getMedium("vacuums");
  TGeoMedium* vac = gGeoManager->GetMedium("vacuums");
  if (vac == nullptr) geoBuild->createMedium(ShipMedium);
  vac = gGeoManager->GetMedium("vacuums");
  gGeoManager->GetTopVolume();
  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  Double_t zLoc;
  if (fzPos > 1E8) {
    // Add thin sensitive plane after hadron absorber
    Float_t distance = 1.;
    Double_t local[3] = {0, 0, 0};
    if (!nav->cd("/MuonShieldArea_1/AbsorberVol_1")) {
      nav->cd("/MuonShieldArea_1/MagnAbsorb_MagRetL_1");
      distance = -1.;
    }
    TGeoBBox* tmp =
        dynamic_cast<TGeoBBox*>(nav->GetCurrentNode()->GetVolume()->GetShape());
    local[2] = distance * tmp->GetDZ();
    Double_t global[3] = {0, 0, 0};
    nav->LocalToMaster(local, global);
    zLoc = global[2] + distance * 1. * cm;
  } else {
    zLoc = fzPos;
  }  // use external input

  TString myname(this->GetName());
  TString shapename_prefix(myname);  // Use a prefix for shapenames

  Double_t xLocPlane = 0.0;
  Double_t yLocPlane = 0.0;
  Double_t zLocPlane = zLoc;

  if (!fCylindricalPlane) {
    TGeoVolume* sensPlane =
        gGeoManager->MakeBox(shapename_prefix + fVetoName + "_box", vac,
                             3.56 * m - 1. * mm, 1.7 * m - 1. * mm, 1. * mm);
    std::cout << this->GetName()
              << ", ConstructGeometry(): Created Box with dimensions: "
                 "3.56*m-1.*mm,1.7*m-1.*mm,1.*mm"
              << std::endl;

    if (!fUseCaveCoordinates) {
      nav->cd("/MuonShieldArea_1/");
    } else {
      Double_t local[3] = {0, 0, zLoc};
      Double_t global[3];
      nav->cd("/target_vacuum_box_1/TargetArea_1");
      nav->LocalToMaster(local, global);
      nav->cd("/cave_1");
      yLocPlane = global[1];
      zLocPlane = global[2];
      xLocPlane = global[0];
    }
    sensPlane->SetLineColor(kBlue - 10);
    nav->GetCurrentNode()->GetVolume()->AddNode(
        sensPlane, 1, new TGeoTranslation(xLocPlane, yLocPlane, zLocPlane));
    fPlaneVolName = sensPlane->GetName();
    AddSensitiveVolume(sensPlane);
  } else {  // add cylindrical sensPlane
    TGeoVolume* sensPlaneCyl =
        gGeoManager->MakeTube(shapename_prefix + fVetoName + "_tube", vac,
                              12.51 * cm, 12.52 * cm, zLoc / 2.);
    std::cout << this->GetName()
              << ", ConstructGeometry(): Created Tube with dimensions: "
                 "12.51*cm,12.52*cm,zLoc/2."
              << std::endl;
    nav->cd("/target_vacuum_box_1/TargetArea_1/HeVolume_1");
    nav->GetCurrentNode()->GetVolume()->AddNode(sensPlaneCyl, 1,
                                                new TGeoTranslation(0, 0, 0));
    fPlaneVolName = sensPlaneCyl->GetName();
    AddSensitiveVolume(sensPlaneCyl);
  }
  // Keep in sync with the per-step splitting guard in ProcessHits().
  if ((fNsplits > 0) && (fIntermediateNsplits > 0) && (!fSplitOnce)) {
    TString parentVolumeName = "/target_vacuum_box_1";
    nav->cd(parentVolumeName.Data());
    TGeoVolume* vol = nav->GetCurrentNode()->GetVolume();
    AddSensitiveVolume(vol);
    // register each unique daughter volume
    RegisterDaughtersRecursively(vol, this);
  }
}

void exitHadronAbsorber::Register() {
  fDetPoints = new std::vector<vetoPoint>();
  TString name = fVetoName + "Point";
  FairRootManager::Instance()->RegisterAny(name.Data(), fDetPoints, kTRUE);
}
