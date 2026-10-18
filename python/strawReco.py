# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""ACTS-based straw tracker reconstruction utilities.

Fit straw-tube track candidates and vertices with ACTS, and extrapolate
fitted tracks to SBT hits for veto matching. The fitting itself is done by
the C++ ``SHiP::ActsStrawTracker``; everything here is in the SHiP frame
(cm, GeV).
"""

import logging
from dataclasses import dataclass

import ROOT
from recoConstants import MIN_HITS_PER_TRACK

logger = logging.getLogger(__name__)

# Track-quality cut for the tracks handed to the vertex fit.
MAX_CHI2_NDF = 25.0

# Number of good tracks the vertex fit is run for.
MIN_VERTEX_TRACKS = 2
MAX_VERTEX_TRACKS = 4

# Distance reported for tracks with no SBT match, as in the GenFit path
NO_VETO_MATCH = (-1, 99999.0)


@dataclass(frozen=True)
class StrawHit:
    """A smeared straw hit, with the MC truth needed for seeding and links."""

    detector_id: int
    station: int
    view: int
    layer: int
    track_id: int
    # MC truth position (cm)
    x: float
    y: float
    z: float
    # Smeared drift distance (cm)
    drift: float
    # Wire end points in x and y (cm)
    xtop: float
    ytop: float
    xbot: float
    ybot: float

    @property
    def layer_key(self) -> tuple[int, int, int]:
        """The straw layer, which can hold at most one hit of a track."""
        return (self.station, self.view, self.layer)

    def drift_sign(self) -> float:
        """Side of the wire the track passed on, taken from the MC truth.

        This resolves the left/right ambiguity with truth information. It
        should be replaced by a refit that uses the residuals.
        """
        wire_x = (self.xtop + self.xbot) / 2.0
        wire_y = (self.ytop + self.ybot) / 2.0
        # Normal to the wire in the x-y plane
        nx = -(self.ybot - self.ytop)
        ny = self.xbot - self.xtop
        return 1.0 if (self.x - wire_x) * nx + (self.y - wire_y) * ny > 0 else -1.0


def make_tracker(geometry, field):
    """Create the ACTS straw tracker for the loaded geometry and field."""
    if not hasattr(ROOT.SHiP, "ActsStrawTracker"):
        raise RuntimeError("FairShip was built without ACTS, so the ACTS track fitter is not available")
    tracker = ROOT.SHiP.ActsStrawTracker(geometry, field)
    logger.info("ACTS straw tracker built with %d straws", tracker.GetNStraws())
    return tracker


def runTracking(tracker, candidates, hits, resolution, fit_vertex=True):
    """Fit track candidates and, if the event qualifies, their vertex.

    ``candidates`` are dicts with ``pos``, ``mom`` (TVector3, SHiP frame),
    ``charge`` and ``indices`` into ``hits``. Each candidate's indices are
    sorted by hit z in place.

    Returns the fitted tracks (``SHiP::RecoTrack``, in the order of the
    tracker's track indices), the fitted vertices (``SHiP::RecoVertex``) and,
    per fitted track, the indices into ``hits`` that were used in the fit.
    """
    tracker.ClearEvent()
    measurements = [tracker.AddMeasurement(h.detector_id, h.drift_sign() * h.drift, resolution) for h in hits]

    track_hit_indices = []
    for cand in candidates:
        cand["indices"].sort(key=lambda i: hits[i].z)

        # The Kalman filter takes at most one measurement per straw layer
        used = []
        seen_layers = set()
        for idx in cand["indices"]:
            if measurements[idx] < 0:
                logger.warning("No ACTS surface for straw %d", hits[idx].detector_id)
                continue
            if hits[idx].layer_key not in seen_layers:
                used.append(idx)
                seen_layers.add(hits[idx].layer_key)

        if len(used) < MIN_HITS_PER_TRACK:
            logger.debug("Skipping track with too few hits: %d", len(used))
            continue

        track_measurements = ROOT.std.vector("int")([measurements[i] for i in used])
        track = tracker.FitTrack(track_measurements, cand["pos"], cand["mom"], round(cand["charge"]))
        if track >= 0:
            track_hit_indices.append(used)

    tracks = [tracker.GetTrack(i) for i in range(tracker.GetNTracks())]

    good = [
        i
        for i, track in enumerate(tracks)
        if track.nMeasurements() >= MIN_HITS_PER_TRACK
        and track.nDoF() > 0
        and track.chi2() / track.nDoF() <= MAX_CHI2_NDF
    ]
    has_pos = any(tracks[i].charge() > 0 for i in good)
    has_neg = any(tracks[i].charge() < 0 for i in good)

    vertices = []
    if fit_vertex and MIN_VERTEX_TRACKS <= len(good) <= MAX_VERTEX_TRACKS and has_pos and has_neg:
        vertex = ROOT.SHiP.RecoVertex()
        if tracker.FitVertex(ROOT.std.vector("int")(good), vertex):
            vertices.append(vertex)
        else:
            logger.debug("Vertex fit failed for tracks %s", good)

    return tracks, vertices, track_hit_indices


def calculateSBTDOCA(tracker, sbt_digis, selected_indices):
    """Match fitted tracks to SBT hits.

    Each track is extrapolated to the plane of constant z through every SBT
    hit. Returns one ``(hitID, distMin)`` per entry of ``selected_indices``,
    with the distance in cm, to match the GenFit
    ShipDigiReco.findVetoHitOnTrack; tracks with no match get
    ``NO_VETO_MATCH``.
    """
    hits = [ROOT.TVector3(hit.GetX(), hit.GetY(), hit.GetZ()) for hit in sbt_digis]
    veto_results = []
    for track in selected_indices:
        hitID, distMin = NO_VETO_MATCH
        for s_idx, hit in enumerate(hits):
            doca = tracker.DistanceToHit(int(track), hit)
            if 0 <= doca < distMin:
                hitID, distMin = s_idx, doca
        veto_results.append((hitID, distMin))
    return veto_results
