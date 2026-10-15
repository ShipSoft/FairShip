# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import math
from types import SimpleNamespace

import pytest
import ROOT
from experimental import analysis_toolkit

TARGET_Z0 = -3500.0


class FakeCandidate:
    """Stand-in for ShipParticle: a vertex and a momentum."""

    def __init__(self, vertex, momentum):
        self.vertex = vertex
        self.momentum = momentum

    def GetVertex(self, v):
        v.SetXYZ(*self.vertex)

    def Momentum(self, p):
        p.SetPxPyPzE(*self.momentum, 10.0)


@pytest.fixture
def selection():
    sel = analysis_toolkit.selection_check.__new__(analysis_toolkit.selection_check)
    sel.ship_geo = SimpleNamespace(target=SimpleNamespace(z0=TARGET_Z0))
    return sel


def test_candidate_pointing_at_target(selection):
    candidate = FakeCandidate((10.0, -20.0, 5000.0), (10.0, -20.0, 5000.0 - TARGET_Z0))
    assert selection.impact_parameter(candidate) == pytest.approx(0.0, abs=1e-9)
    assert selection.impact_parameter_xy(candidate) == pytest.approx((0.0, 0.0), abs=1e-9)


def test_parallel_to_beam_axis(selection):
    # A line parallel to z passes the target point at the vertex's transverse offset.
    candidate = FakeCandidate((3.0, -4.0, 5000.0), (0.0, 0.0, 50.0))
    assert selection.impact_parameter(candidate) == pytest.approx(5.0)
    assert selection.impact_parameter_xy(candidate) == pytest.approx((-3.0, 4.0))


def test_components_add_up_to_impact_parameter(selection):
    candidate = FakeCandidate((40.0, 120.0, 6000.0), (0.3, -0.7, 40.0))
    ip = selection.impact_parameter_vector(candidate)
    x, y = selection.impact_parameter_xy(candidate)
    assert (x, y) == (ip.X(), ip.Y())
    assert math.hypot(x, y, ip.Z()) == pytest.approx(selection.impact_parameter(candidate))
    # The vector is perpendicular to the line of flight.
    assert ip.Dot(ROOT.TVector3(0.3, -0.7, 40.0).Unit()) == pytest.approx(0.0, abs=1e-9)
