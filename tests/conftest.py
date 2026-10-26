# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import pytest


# Session scope: loading libShipData a second time in one process crashes in
# ROOT 6.40, so every test module that needs it has to share this one load.
@pytest.fixture(scope="session")
def root_with_shipdata():
    ROOT = pytest.importorskip("ROOT")
    if ROOT.gSystem.Load("libShipData") < 0:
        pytest.skip("libShipData not available")
    return ROOT


# libCaloScoringPlane links libShipData. Request root_with_shipdata first so
# that libShipData is loaded by that one fixture and not again later.
@pytest.fixture(scope="session")
def root_with_calo_scoring_plane(root_with_shipdata):
    ROOT = root_with_shipdata
    if ROOT.gSystem.Load("libCaloScoringPlane") < 0:
        pytest.skip("libCaloScoringPlane not available")
    return ROOT
