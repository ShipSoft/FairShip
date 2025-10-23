def find_shield_center(ship_geo):
    zEndOfPassiveShield = ship_geo.muShield.z
    dZ = [None] * 7
    Z = [None] * 7
    zgap = 10.
    dZ[0] = ship_geo.muShield.dZ1 - zgap / 2
    Z[0] = zEndOfPassiveShield + dZ[0] + zgap

    dZ[1] = ship_geo.muShield.dZ2 - zgap / 2
    Z[1] = Z[0] + dZ[0] + dZ[1] + zgap

    dZ[2] = ship_geo.muShield.dZ3 - zgap / 2
    Z[2] = Z[1] + dZ[1] + dZ[2] + 2 * zgap

    dZ[3] = ship_geo.muShield.dZ4 - zgap / 2
    Z[3] = Z[2] + dZ[2] + dZ[3] + zgap

    dZ[4] = ship_geo.muShield.dZ5 - zgap / 2
    Z[4] = Z[3] + dZ[3] + dZ[4] + zgap

    dZ[5] = ship_geo.muShield.dZ6 - zgap / 2
    Z[5] = Z[4] + dZ[4] + dZ[5] + zgap

    dZ[6] = ship_geo.muShield.dZ7 - zgap / 2
    Z[6] = Z[5] + dZ[5] + dZ[6] + zgap


    shield_center = (Z[1] + Z[6] + dZ[6] - dZ[1]) / 2
    shield_half_length = abs((Z[1] - dZ[1]) - (Z[6] + dZ[6])) / 2
    return shield_center, shield_half_length, Z
