# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Check that the ECN3 cross-section of the geometry configuration is that of ShipCave.

ShipCave builds the cavern from the constants in passive/ShipCavernLayout.h,
while geometry_config places the UBT and its scoring planes from its own copy
of the ECN3 floor and side walls. Nothing else ties the two together, so if one
changed without the other, the UBT would stand off the floor or the scoring
planes would cut into the walls without any error.
"""

import re
from pathlib import Path

import geometry_config
import pytest
import shipunit as u

LAYOUT = Path(__file__).resolve().parent.parent / "passive" / "ShipCavernLayout.h"

# geometry_config name -> ShipCavernLayout constant
QUANTITIES = {
    "ECN3LeftX": "kECN3LeftX",
    "ECN3RightX": "kECN3RightX",
    "ECN3FloorY": "kECN3FloorY",
}


def layout_constants() -> dict[str, float]:
    """The constants of ShipCavernLayout.h, in FairShip length units."""
    pattern = re.compile(r"(k\w+)\s*=\s*(-?[\d.]+)\s*\*\s*ShipUnit::m\b")
    return {name: float(value) * u.m for name, value in pattern.findall(LAYOUT.read_text())}


@pytest.mark.parametrize("quantity", QUANTITIES)
def test_ecn3_cross_section_matches_ship_cave(quantity):
    constants = layout_constants()
    cave = geometry_config.create_config().cave
    assert cave[quantity] == pytest.approx(constants[QUANTITIES[quantity]], abs=1.0e-6 * u.cm)
