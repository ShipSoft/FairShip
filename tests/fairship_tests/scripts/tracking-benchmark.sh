#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

set -euo pipefail

export QT_QPA_PLATFORM=offscreen

python "$FAIRSHIP_ROOT/macro/run_tracking_benchmark.py" \
    -n 1000 \
    --seed 42 \
    --debug 0 \
    --tag tracking_benchmark \
    --output-json tracking_metrics.json \
    --pID 13 \
    --Estart 1.0 \
    --Eend 100.0 \
    --Vz 8300.0 \
    --Dx 200.0 \
    --Dy 300.0 \
    --nTracks 1
