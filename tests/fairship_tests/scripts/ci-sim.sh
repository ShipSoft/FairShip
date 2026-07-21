#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

set -euo pipefail

export QT_QPA_PLATFORM=offscreen

python "$FAIRSHIP_ROOT/macro/run_simScript.py" \
    --test \
    --debug 2 \
    --vacuums \
    --SND \
    --SND_design=all \
    --shieldName TRY_2025 \
    --EvtGenDecayer \
    --seed 42 \
    --tag ci-test
