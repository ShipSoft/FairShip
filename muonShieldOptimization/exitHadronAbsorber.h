// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
#define MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_

#include <cstddef>
#include <map>
#include <set>
#include <utility>
#include <vector>

#include "Detector.h"
#include "TFile.h"
#include "TNtuple.h"
#include "vetoPoint.h"

class FairVolume;

struct TrackBuffer {
  Int_t pdg;
  Double_t px, py, pz, e;
  Double_t x, y, z, t;
  Double_t polx, poly, polz;
  Double_t weight;
  Int_t parentID;
  // A continuation of a per-step split track rather than a clone: it is
  // transported normally instead of being forced to decay at once.
  Bool_t continuation = kFALSE;
  // Split set of the split track and the role of this entry in it
  // (ShipMCTrack::SplitRole), recorded on the stack when it is pushed.
  Int_t splitSet = -1;
  Int_t splitRole = 0;
};

class exitHadronAbsorber : public SHiP::Detector<vetoPoint> {
 public:
  exitHadronAbsorber(const char* Name, Bool_t Active);
  exitHadronAbsorber();

  // Number of stack entries each pending split clone is assumed to add to the
  // event once it has decayed and its products have showered. This is an
  // empirical, conservative estimate from production runs with per-step
  // splitting. It projects the event size that --max-event-size is checked
  // against, and run_fixedTarget.py uses it to validate that option.
  static constexpr std::size_t kShowerSafetyFactor = 500;

  void Initialize() override;

  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  void Register() override;

  void ConstructGeometry() override;

  void FinishRun() override;
  void PreTrack() override;
  void PostTrack() override;
  void BeginEvent() override;
  void FinishEvent() override;

  void SetNSplits(Int_t n) { fNsplits = n; }
  void SetIntermediateNSplits(Int_t n) { fIntermediateNsplits = n; }
  void SetMaxSplitBuffer(Int_t n);
  void SetMaxEventSize(Int_t n);
  void SetSplitMultipleTimes() { fSplitOnce = kFALSE; }

  inline void SetEnergyCut(Float_t emax) { EMax = emax; }
  inline void SetOnlyMuons() { fOnlyMuons = kTRUE; }
  inline void SetOpt4DP() { withNtuple = kTRUE; }
  inline void SkipNeutrinos() { fSkipNeutrinos = kTRUE; }
  inline void SetZposition(Float_t x) { fzPos = x; }
  inline void SetVetoPointName(TString name) { fVetoName = std::move(name); }
  inline void SetCylindricalPlane() { fCylindricalPlane = kTRUE; }
  inline void SetUseCaveCoordinates() { fUseCaveCoordinates = kTRUE; }

 private:
  // Hand the buffered clones of a splitting decay to the stack popper. They
  // can only be popped during a step, so the first track after the decay is
  // designated as their carrier and must not be stopped before it steps.
  // The designation is shared by all instances: run_fixedTarget can add
  // several sensitive planes and whichever is polled first would otherwise
  // stop the carrier before the splitting instance ever sees it.
  static constexpr Int_t kNoCarrier = -1;
  static constexpr Int_t kCarrierRequested = -2;
  static Int_t fgCarrierTrackID;  //!

  // Ask for the next track to carry the clones just added to the buffer.
  static void RequestCloneCarrier() { fgCarrierTrackID = kCarrierRequested; }

  // A decay that the clones re-sample is replaced as a whole: its products,
  // and everything they go on to make, would otherwise be counted on top of
  // the same channels from the clones. Shared by all instances for the same
  // reason as the carrier: a sibling plane must not score them either.
  static std::set<Int_t> fgReplacedDecays;  //! split tracks whose decay the
                                            //! clones replace
  static std::set<Int_t> fgReplacedTracks;  //! products of those decays and
                                            //! their descendants

  // Weight of a per-step split track along its path. Geant4 hands a track's
  // secondaries to the stack only once the track is done, and ShipStack then
  // scales them by its final weight, although one made mid-track should carry
  // the weight the track had when it made it. PreTrack() puts that right from
  // this history. Shared by all instances, because the first plane to run
  // PreTrack() for a secondary has to see it.
  struct WeightHistory {
    Double_t initial = 1.;  ///< weight before the first split
    /// (time at the end of the split step, weight after the split), in step
    /// order and so strictly increasing in time
    std::vector<std::pair<Double_t, Double_t>> splits;
    /// Weight of the track at time t; a secondary made exactly at the end of
    /// a split step, e.g. by the interaction that ends the track, survived
    /// that step's decay probability and gets the weight after the split.
    Double_t WeightAt(Double_t t) const;
  };
  static std::map<Int_t, WeightHistory> fgWeightHistory;  //!
  static std::set<Int_t> fgWeightCorrected;  //! secondaries already rescaled

  // Drop the clones still buffered at the end of an event or run, keeping
  // track of how much weight was never simulated.
  void DiscardBufferedClones();

  // Split set of a track that is being split, created on first use. The
  // track is recorded on the stack as the survivor of its set; its clones
  // and continuations join the same set. A continuation maps to the set of
  // the track it continues, so a per-step split track keeps one set along its
  // whole path. The set's weight is the track's weight when the set is
  // created, before any split lowers it.
  Int_t SplitSetOf(Int_t trackId, Double_t weight);

  Int_t fUniqueID = 0;
  Bool_t fOnlyMuons;         //! flag if only muons should be stored
  Bool_t fSkipNeutrinos;     //! flag if neutrinos should be ignored
  TString fVetoName;         // name to save veto collection
  TString fPlaneVolName;     //! name of the sensitive plane volume
  Double_t fzPos;            //!  zPos, optional
  Bool_t withNtuple;         //! special option for Dark Photon physics studies
  TNtuple* fNtuple;          //!
  Float_t EMax = 0.;         //! max energy to transport
  Bool_t fCylindricalPlane;  //! cylindrical sensPlane flag
  Bool_t fUseCaveCoordinates = kFALSE;  //! set position from cave

  int32_t fNsplits;
  // intermediate splits to use at each step before the particle decays
  int32_t fIntermediateNsplits;
  // Upper bound on the clone buffer, in both splitting modes. Per-step
  // splitting is the pathological case: the buffer grows by
  // fIntermediateNsplits on every qualifying step and is only drained in
  // PreTrack(), so a bad split count could make it grow without bound within a
  // single track. ~25k TrackBuffer records is about 2.5 MB, far above what any
  // sane configuration reaches. Set via --max-split-buffer.
  // This is a hard bound: ProcessHits() stops accepting per-step clones early
  // enough to leave room for the fNsplits endpoint clones PostTrack() appends,
  // and Initialize() rejects a cap that fNsplits alone would exceed.
  std::size_t fMaxSplitBuffer = 25'000;
  // Upper bound on the projected event size: the stack size plus
  // kShowerSafetyFactor entries for every pending clone. With the defaults this
  // is the cap that stops per-step splitting, at about 10k pending clones.
  // Set via --max-event-size.
  std::size_t fMaxEventSize = 5'000'000;
  // latches so each cap is reported at most once per event
  Bool_t fSplitBufferLimitWarned = kFALSE;  //!
  Bool_t fEventSizeLimitWarned = kFALSE;    //!
  Bool_t fSplitOnce =
      kTRUE;  // determine if we want to split once (when the particle decays)
              // or at every step (taking decay probabilities into account)

  std::vector<TrackBuffer> fSecondaryBuffer;
  std::set<Int_t> fCloneTracks;
  // The last per-step split, so that PostTrack() can tell whether the step on
  // which a track decayed was split.
  Int_t fLastSplitTrackID = -1;  //!
  Int_t fLastSplitStep = -1;     //!
  // Split set per stack index of a split track or continuation, and the next
  // free set ID in the event.
  std::map<Int_t, Int_t> fSplitSetOfTrack;  //!
  std::vector<Double_t> fSplitSetWeight;    //! indexed by set ID
  Int_t fNextSplitSet = 0;                  //!

  Int_t fSplitDecays = 0;          //! decays replaced by clones
  Int_t fClonesBuffered = 0;       //! clones created for those decays
  Int_t fContinuedDecays = 0;      //! natural decays replaced by a continuation
  Int_t fLostBufferEvents = 0;     //! events ending with unflushed clones
  Int_t fLostCloneTracks = 0;      //! clones which were never tracked
  Double_t fLostCloneWeight = 0.;  //! summed weight of those clones

  TFile* fout;               //!
  TClonesArray* fElectrons;  //!
  Int_t index;
};

#endif  // MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
