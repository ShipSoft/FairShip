#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

set -euo pipefail

export QT_QPA_PLATFORM=offscreen

python "$FAIRSHIP_ROOT/macro/run_simScript.py" \
    --Pythia8 \
    -t \
    -n 100 \
    --debug 0 \
    --tag pythia8_summary \
    --seed 42 \
    --validation
