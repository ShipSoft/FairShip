# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Hit bookkeeping of the ACTS straw reconstruction, with a stand-in tracker."""

import ROOT
from recoConstants import MIN_HITS_PER_TRACK
from strawReco import StrawHit, runTracking

UNKNOWN_STRAW = -1


def make_hit(detector_id, station, view, layer, z, x=1.0, track_id=0):
    # A vertical wire at x = 0, so the side is the sign of x
    return StrawHit(
        detector_id=detector_id,
        station=station,
        view=view,
        layer=layer,
        track_id=track_id,
        x=x,
        y=0.0,
        z=z,
        drift=0.5,
        xtop=0.0,
        ytop=1.0,
        xbot=0.0,
        ybot=-1.0,
    )


class FakeTrack:
    def nMeasurements(self):
        return MIN_HITS_PER_TRACK

    def nDoF(self):
        return 1.0

    def chi2(self):
        return 1.0

    def charge(self):
        return 1


class FakeTracker:
    """Records what runTracking hands to SHiP::ActsStrawTracker."""

    def __init__(self):
        self.measurements = []
        self.fits = []

    def ClearEvent(self):
        self.measurements.clear()
        self.fits.clear()

    def AddMeasurement(self, detector_id, drift, resolution):
        if detector_id == UNKNOWN_STRAW:
            return -1
        self.measurements.append((detector_id, drift, resolution))
        return len(self.measurements) - 1

    def FitTrack(self, measurements, pos, mom, charge):
        self.fits.append(list(measurements))
        return len(self.fits) - 1

    def GetNTracks(self):
        return len(self.fits)

    def GetTrack(self, index):
        return FakeTrack()


def candidate(indices):
    return {"pos": ROOT.TVector3(), "mom": ROOT.TVector3(0, 0, 10), "charge": 1.0, "indices": indices}


def test_measurements_follow_hits_in_z_with_one_per_layer():
    # Hit 0 is an unknown straw, so measurement indices are hit indices - 1.
    # The last hit shares a straw layer with hit 2 but sits at smaller z, so
    # it is kept and hit 2 is not.
    hits = [make_hit(UNKNOWN_STRAW, 1, 0, 0, z=0.0)]
    hits += [make_hit(1000 + i, 1, i // 2, i % 2, z=10.0 * i) for i in range(MIN_HITS_PER_TRACK + 1)]
    hits.append(make_hit(9999, 1, 0, 1, z=5.0))
    tracker = FakeTracker()
    tracks, vertices, hit_indices = runTracking(
        tracker, [candidate(list(reversed(range(len(hits)))))], hits, 0.012, fit_vertex=False
    )

    assert len(tracks) == 1
    assert vertices == []
    used = hit_indices[0]
    assert used == sorted(used, key=lambda i: hits[i].z)
    assert 0 not in used
    assert len({hits[i].layer_key for i in used}) == len(used)
    assert len(hits) - 1 in used and 2 not in used
    # The fitter sees the measurements of exactly those hits
    assert tracker.fits[0] == [i - 1 for i in used]
    assert [tracker.measurements[m][0] for m in tracker.fits[0]] == [hits[i].detector_id for i in used]


def test_too_few_hits_are_not_fitted():
    hits = [make_hit(1000 + i, 1, 0, i, z=float(i)) for i in range(2)]
    tracker = FakeTracker()
    tracks, _, hit_indices = runTracking(tracker, [candidate([0, 1])], hits, 0.012, fit_vertex=False)
    assert tracks == [] and hit_indices == [] and tracker.fits == []


def test_drift_sign_follows_the_side_of_the_wire():
    left = make_hit(1000, 1, 0, 0, z=0.0, x=1.0)
    right = make_hit(1000, 1, 0, 0, z=0.0, x=-1.0)
    assert left.drift_sign() == -right.drift_sign()
