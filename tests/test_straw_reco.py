# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Hit bookkeeping of the ACTS straw reconstruction, with a stand-in tracker."""

from recoConstants import MIN_HITS_PER_TRACK
from strawReco import StrawHit, runTracking

UNKNOWN_STRAW = -1


def make_hit(detector_id, station, view, layer, z, drift=0.5, track_id=0):
    return StrawHit(
        detector_id=detector_id,
        station=station,
        view=view,
        layer=layer,
        track_id=track_id,
        z=z,
        drift=drift,
    )


class FakeTrack:
    def __init__(self, charge=1):
        self._charge = charge

    def nMeasurements(self):
        return MIN_HITS_PER_TRACK

    def nDoF(self):
        return 1.0

    def chi2(self):
        return 1.0

    def charge(self):
        return self._charge

    def SetTrackLength(self, length):
        self.track_length = length

    def SetUBTExtrapolation(self, position, momentum, covariance, path_length):
        self.ubt = (position.Z(), path_length)

    def SetTDExtrapolation(self, position, momentum, covariance, path_length):
        self.td = (position.Z(), path_length)


class FakeTracker:
    """Records what runTracking hands to SHiP::ActsStrawTracker.

    FitCandidate drops the last measurement of each candidate, as the real
    tracker drops measurements that do not fit the track.
    """

    def __init__(self, found=(), charges=(), unreachable_z=()):
        self.measurements = []
        self.candidates = []
        self.tracks = []
        self.vertices = []
        self._found = found
        self._charges = charges
        self._unreachable_z = unreachable_z
        self.extrapolations = []

    def ClearEvent(self):
        self.measurements.clear()
        self.tracks.clear()

    def AddMeasurement(self, detector_id, drift, resolution):
        if detector_id == UNKNOWN_STRAW:
            return -1
        self.measurements.append((detector_id, drift, resolution))
        return len(self.measurements) - 1

    def FindTracks(self):
        self.tracks = [list(t) for t in self._found]
        return len(self.tracks)

    def FitCandidate(self, measurements):
        self.candidates.append(list(measurements))
        self.tracks.append(list(measurements)[:-1])
        return len(self.tracks) - 1

    def GetNTracks(self):
        return len(self.tracks)

    def GetTrack(self, index):
        return FakeTrack(self._charges[index] if self._charges else 1)

    def GetTrackMeasurements(self, index):
        return self.tracks[index]

    def TrackLength(self, index):
        return 100.0 + index

    def ExtrapolateToZ(self, index, z, from_last_hit, position, momentum, covariance, path_length):
        self.extrapolations.append((index, z, from_last_hit))
        if z in self._unreachable_z:
            return False
        position.SetXYZ(0.0, 0.0, z)
        path_length.value = z / 10.0
        return True

    def FitVertex(self, tracks, vertex):
        self.vertices.append(list(tracks))
        return True


def test_candidate_hits_are_ordered_in_z_with_one_per_layer():
    # Hit 0 is an unknown straw, so measurement indices are hit indices - 1.
    # The last hit shares a straw layer with hit 2 but sits at smaller z, so
    # it is kept and hit 2 is not.
    hits = [make_hit(UNKNOWN_STRAW, 1, 0, 0, z=0.0)]
    hits += [make_hit(1000 + i, 1, i // 2, i % 2, z=10.0 * i) for i in range(MIN_HITS_PER_TRACK + 1)]
    hits.append(make_hit(9999, 1, 0, 1, z=5.0))
    tracker = FakeTracker()
    tracks, vertices, hit_indices = runTracking(
        tracker, [{"indices": list(reversed(range(len(hits))))}], hits, 0.012, fit_vertex=False
    )

    assert len(tracks) == 1
    assert vertices == []
    used = [m + 1 for m in tracker.candidates[0]]
    assert used == sorted(used, key=lambda i: hits[i].z)
    assert 0 not in used
    assert len({hits[i].layer_key for i in used}) == len(used)
    assert len(hits) - 1 in used and 2 not in used
    # The hit indices of the track are those the tracker kept
    assert hit_indices[0] == used[:-1]


def test_drift_distances_are_passed_unsigned():
    hits = [make_hit(1000 + i, 1, i // 2, i % 2, z=float(i), drift=0.1 * i) for i in range(MIN_HITS_PER_TRACK)]
    tracker = FakeTracker()
    runTracking(tracker, [{"indices": list(range(len(hits)))}], hits, 0.012, fit_vertex=False)
    assert [m[1] for m in tracker.measurements] == [h.drift for h in hits]


def test_too_few_hits_are_not_fitted():
    hits = [make_hit(1000 + i, 1, 0, i, z=float(i)) for i in range(2)]
    tracker = FakeTracker()
    tracks, _, hit_indices = runTracking(tracker, [{"indices": [0, 1]}], hits, 0.012, fit_vertex=False)
    assert tracks == [] and hit_indices == [] and tracker.candidates == []


def test_found_tracks_map_back_to_hits():
    # With no candidates, the tracker finds the tracks itself
    hits = [make_hit(UNKNOWN_STRAW, 1, 0, 0, z=0.0)] + [make_hit(1000 + i, 1, 0, 0, z=float(i)) for i in range(4)]
    tracker = FakeTracker(found=[[0, 2], [1, 3]])
    tracks, _, hit_indices = runTracking(tracker, None, hits, 0.012, fit_vertex=False)
    assert len(tracks) == 2
    assert hit_indices == [[1, 3], [2, 4]]


def test_vertices_are_fitted_for_opposite_charge_pairs():
    hits = [make_hit(1000 + i, 1, 0, 0, z=float(i)) for i in range(3)]
    tracker = FakeTracker(found=[[0], [1], [2]], charges=[1, -1, 1])
    _, vertices, _ = runTracking(tracker, None, hits, 0.012, fit_vertex=True)
    assert tracker.vertices == [[0, 1], [1, 2]]
    assert len(vertices) == 2


def test_extrapolations_and_track_length_are_stored():
    # The UBT is reached backwards from the first hit, the timing detector
    # forwards from the last; a plane the track cannot reach is not stored
    hits = [make_hit(1000 + i, 1, 0, 0, z=float(i)) for i in range(2)]
    tracker = FakeTracker(found=[[0], [1]], unreachable_z=(9000.0,))
    tracks, _, _ = runTracking(tracker, None, hits, 0.012, fit_vertex=False, ubt_z=3000.0, td_z=9000.0)
    assert tracker.extrapolations == [(0, 3000.0, False), (0, 9000.0, True), (1, 3000.0, False), (1, 9000.0, True)]
    assert [t.track_length for t in tracks] == [100.0, 101.0]
    assert all(t.ubt == (3000.0, 300.0) for t in tracks)
    assert not any(hasattr(t, "td") for t in tracks)


def test_planes_of_missing_detectors_are_not_extrapolated():
    hits = [make_hit(1000, 1, 0, 0, z=0.0)]
    tracker = FakeTracker(found=[[0]])
    tracks, _, _ = runTracking(tracker, None, hits, 0.012, fit_vertex=False)
    assert tracker.extrapolations == []
    assert tracks[0].track_length == 100.0
    assert not hasattr(tracks[0], "ubt") and not hasattr(tracks[0], "td")


def test_vertex_of_all_tracks_is_added_on_request():
    hits = [make_hit(1000 + i, 1, 0, 0, z=float(i)) for i in range(3)]
    tracker = FakeTracker(found=[[0], [1], [2]], charges=[1, -1, 1])
    _, vertices, _ = runTracking(tracker, None, hits, 0.012, fit_vertex=True, vertex_all_tracks=True)
    assert tracker.vertices == [[0, 1], [1, 2], [0, 1, 2]]
    assert len(vertices) == 3


def test_vertex_of_two_tracks_is_not_repeated():
    hits = [make_hit(1000 + i, 1, 0, 0, z=float(i)) for i in range(2)]
    tracker = FakeTracker(found=[[0], [1]], charges=[1, -1])
    runTracking(tracker, None, hits, 0.012, fit_vertex=True, vertex_all_tracks=True)
    assert tracker.vertices == [[0, 1]]


def test_vertex_of_two_same_charge_tracks_is_fitted_on_request():
    hits = [make_hit(1000 + i, 1, 0, 0, z=float(i)) for i in range(2)]
    tracker = FakeTracker(found=[[0], [1]], charges=[1, 1])
    runTracking(tracker, None, hits, 0.012, fit_vertex=True, vertex_all_tracks=True)
    assert tracker.vertices == [[0, 1]]
