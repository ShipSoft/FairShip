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
