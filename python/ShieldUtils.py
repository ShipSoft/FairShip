# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

def find_shield_center(ship_geo):
    return ship_geo.muShield.z + ship_geo.muShield.length/2, ship_geo.muShield.length/2
