# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from types import SimpleNamespace

import pytest
import ROOT
import shipVeto


class _Digi:
    def __init__(self, det_id) -> None:
        self.det_id = det_id

    def GetDetectorID(self):
        return self.det_id

    def GetXYZ(self) -> None:
        pass

    def GetEloss(self) -> None:
        pass

    def isValid(self) -> bool:
        return True


class _Point:
    def __init__(self, track_id) -> None:
        self.track_id = track_id

    def GetTrackID(self):
        return self.track_id

    def Momentum(self, mom) -> None:
        mom.SetXYZ(1.0, 0.0, 0.0)


class _FitStatus:
    def isFitConverged(self) -> bool:
        return True

    def getNdf(self) -> int:
        return 30


class _Track:
    def getFitStatus(self):
        return _FitStatus()


@pytest.fixture
def veto():
    # Skip __init__, which needs a geometry in gGeoManager.
    task = shipVeto.Task.__new__(shipVeto.Task)
    task.SBTefficiency = 0.99
    task.UBTefficiency = 0.9
    task.random = ROOT.TRandom3(13)
    # Track 0 is the primary, e.g. the incoming muon of muon DIS.
    task.sTree = SimpleNamespace(
        Digi_SBTHits=[_Digi(1), _Digi(2), _Digi(3)],
        digiSBT2MC=[[0], [0, 5], [5]],
        UpstreamTaggerPoint=[_Point(0), _Point(5), _Point(5)],
        FitTracks=[_Track(), _Track(), _Track(), _Track()],
        fitTrack2MC=[0, 5, 5, 7],
    )
    return task


@pytest.mark.parametrize(
    ("kwargs", "sbt", "ubt", "tracks"),
    [
        ({}, 3, 3, 4),
        ({"only_track": 0}, 2, 1, 1),
        ({"exclude_track": 0}, 1, 2, 3),
        ({"only_track": 5}, 2, 2, 2),
        ({"exclude_track": 5}, 1, 1, 2),
    ],
)
def test_track_filters(veto, kwargs, sbt, ubt, tracks):
    assert veto.SBT_decision(**kwargs)[2] == sbt
    assert veto.UBT_decision(**kwargs)[2] == ubt
    assert veto.Track_decision(**kwargs)[2] == tracks


def test_mcParticle_removed(veto):
    with pytest.raises(TypeError):
        veto.SBT_decision(5)
