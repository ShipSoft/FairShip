# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import pytest
from mc_truth import PRIMARY_PROCESS, find_signal_track, signal_weight


class FakeTrack:
    """Minimal stand-in for ShipMCTrack, so the tests need no ROOT."""

    def __init__(self, pdg, mother, process=PRIMARY_PROCESS, weight=1.0):
        self.pdg = pdg
        self.mother = mother
        self.process = process
        self.weight = weight

    def GetPdgCode(self):
        return self.pdg

    def GetMotherId(self):
        return self.mother

    def GetProcName(self):
        return self.process

    def GetWeight(self):
        return self.weight


# The five MCTrack layouts the SHiP generators produce. Each is (tracks,
# expected signal index); see shipgen/HNLPythia8Generator.cxx:269-283,
# shipgen/DPPythia8Generator.cxx:246-298 and shipgen/EvtCalcGenerator.cxx:205.
LAYOUTS = {
    "hnl_external_charm_file": (
        [
            FakeTrack(2212, -1),  # grand mother from the input file
            FakeTrack(431, 0),  # charm hadron
            FakeTrack(9900015, 1),  # signal
            FakeTrack(13, 2),
            FakeTrack(-211, 2),
        ],
        2,
    ),
    "hnl_no_input_file": (
        [
            FakeTrack(431, -1),  # charm hadron
            FakeTrack(9900015, 0),  # signal
            FakeTrack(13, 1),
            FakeTrack(-211, 1),
        ],
        1,
    ),
    "dark_photon_meson_production": (
        [
            FakeTrack(2212, -1),
            FakeTrack(111, 0),
            FakeTrack(4900023, 1),  # signal
            FakeTrack(13, 2),
            FakeTrack(-13, 2),
        ],
        2,
    ),
    "dark_photon_proton_bremsstrahlung": (
        [
            FakeTrack(9900015, -1),  # signal, no mother stored
            FakeTrack(11, 0),
            FakeTrack(-11, 0),
        ],
        0,
    ),
    "evtcalc_external_llp_file": (
        [
            FakeTrack(999, -1),  # signal, geantino placeholder PDG
            FakeTrack(13, 0),
            FakeTrack(-13, 0),
        ],
        0,
    ),
}


@pytest.mark.parametrize("layout", LAYOUTS)
def test_signal_found_in_every_generator_layout(layout):
    tracks, expected = LAYOUTS[layout]
    assert find_signal_track(tracks) == expected


def test_geant_secondaries_are_ignored():
    """A delta ray crossing the tracker must not be mistaken for a daughter."""
    tracks = [
        FakeTrack(12345678, -1),  # signal from an external file
        FakeTrack(-13, 0),
        FakeTrack(13, 0),
        FakeTrack(11, 2, process="Delta ray"),
        FakeTrack(22, 2, process="Bremstrahlung"),
    ]
    assert find_signal_track(tracks) == 0


def test_explicit_pdg_takes_precedence():
    tracks, _ = LAYOUTS["hnl_external_charm_file"]
    assert find_signal_track(tracks, pdg=9900015) == 2
    # Sign is irrelevant, as elsewhere in the analysis code.
    assert find_signal_track(tracks, pdg=-9900015) == 2


def test_explicit_pdg_absent_returns_none():
    tracks, _ = LAYOUTS["hnl_external_charm_file"]
    assert find_signal_track(tracks, pdg=4900023) is None


def test_single_stored_daughter_still_finds_the_signal():
    """Not every decay product is kept; one daughter must be enough.

    Seen in 7 of 2000 events of the issue-1371 dark-scalar sample.
    """
    tracks = [
        FakeTrack(12345678, -1),  # signal
        FakeTrack(13, 0),  # the only decay product stored
        FakeTrack(11, 1, process="Delta ray"),
    ]
    assert find_signal_track(tracks) == 0


def test_background_cascade_returns_none():
    """A muon-background stack is a branching cascade with several roots."""
    tracks = [
        FakeTrack(2212, -1),
        FakeTrack(2112, -1),  # second root: not a single production chain
        FakeTrack(1, 1),
        FakeTrack(1, 2),
        FakeTrack(213, 3),
        FakeTrack(211, 4),
    ]
    assert find_signal_track(tracks) is None


def test_lone_primary_returns_none():
    """A single generator track with no daughters is not a signal decay."""
    assert find_signal_track([FakeTrack(2212, -1)]) is None


def test_empty_event_returns_none():
    assert find_signal_track([]) is None


def test_signal_weight_reads_the_signal_track():
    tracks = [
        FakeTrack(2212, -1, weight=1.0),  # grandmother, weight hardcoded to 1
        FakeTrack(431, 0, weight=0.25),
        FakeTrack(9900015, 1, weight=0.25),  # signal
        FakeTrack(13, 2, weight=0.25),
        FakeTrack(-211, 2, weight=0.25),
    ]
    assert signal_weight(tracks) == pytest.approx(0.25)


def test_signal_weight_falls_back_when_no_signal():
    tracks = [FakeTrack(2212, -1, weight=0.5), FakeTrack(2112, -1, weight=0.5)]
    assert signal_weight(tracks) == pytest.approx(1.0)


def test_signal_weight_falls_back_on_nonpositive_weight():
    tracks = [
        FakeTrack(9900015, -1, weight=0.0),
        FakeTrack(13, 0),
        FakeTrack(-13, 0),
    ]
    assert signal_weight(tracks) == pytest.approx(1.0)
