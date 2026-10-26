# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Check that the ECN3 cross-section of the geometry configuration is that of ShipCave.

ShipCave builds the cavern from the constants in passive/ShipCavernLayout.h,
while geometry_config places the UBT and its scoring planes from its own copy
of the ECN3 floor and side walls. Nothing else ties the two together, so if one
changed without the other, the UBT would stand off the floor or the scoring
planes would cut into the walls without any error.
"""

from pathlib import Path

import geometry_config
import pytest
import shipunit as u

ROOT = pytest.importorskip("ROOT")

SOURCE = Path(__file__).resolve().parent.parent

# geometry_config name -> ShipCavernLayout constant
QUANTITIES = {
    "ECN3LeftX": "kECN3LeftX",
    "ECN3RightX": "kECN3RightX",
    "ECN3FloorY": "kECN3FloorY",
}


@pytest.fixture(scope="module")
def layout():
    """The ShipCavernLayout namespace, compiled by Cling from the header ShipCave uses."""
    for directory in ("passive", "shipdata"):
        ROOT.gInterpreter.AddIncludePath(str(SOURCE / directory))
    assert ROOT.gInterpreter.Declare('#include "ShipCavernLayout.h"')
    return ROOT.ShipCavernLayout


@pytest.mark.parametrize("quantity", QUANTITIES)
def test_ecn3_cross_section_matches_ship_cave(layout, quantity):
    # Both are in the FairShip length unit.
    cave = geometry_config.create_config().cave
    assert cave[quantity] == pytest.approx(getattr(layout, QUANTITIES[quantity]), abs=1.0e-6 * u.cm)
