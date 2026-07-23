#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

set -euo pipefail

export QT_QPA_PLATFORM=offscreen

python "$FAIRSHIP_ROOT/macro/run_simScript.py" \
    --EvtGenDecayer \
    -t \
    -n 100 \
    --debug 0 \
    --tag evtgen_summary \
    --seed 42 \
    --validation
