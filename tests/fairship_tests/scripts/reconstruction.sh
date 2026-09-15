#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

set -euo pipefail

export QT_QPA_PLATFORM=offscreen

python "$FAIRSHIP_ROOT/macro/ShipReco.py" \
    -f sim_muonback_io.root \
    -g geo_muonback_io.root \
    --patRec AR \
    --Debug
