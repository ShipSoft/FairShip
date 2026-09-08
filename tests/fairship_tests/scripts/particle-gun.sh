#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

set -euo pipefail

export QT_QPA_PLATFORM=offscreen

python "$FAIRSHIP_ROOT/macro/run_simScript.py" \
    --tag particle_gun_io \
    -n 100 \
    -s 42 \
    --debug 0 \
    --vacuums \
    PG \
    --pID 13 \
    --Estart 1.0 \
    --Eend 10.0 \
    --Vz 8300.0 \
    --multiplePG \
    --Dx 50.0 \
    --Dy 50.0
