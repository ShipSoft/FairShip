#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

set -euo pipefail

export QT_QPA_PLATFORM=offscreen

python "$FAIRSHIP_ROOT/macro/run_simScript.py" \
    -n 100 \
    -i 100 \
    -f https://cernbox.cern.ch/remote.php/dav/public-files/vdwtXtgM5P2Z0S5/pythia8_Geant4_10.0_withCharmandBeauty0_mu.root \
    --remote-input \
    --tag muonback_io \
    --sameSeed 42 \
    --seed 42 \
    --MuonBack \
    --FollowMuon \
    --FastMuon \
    --run-number 123 \
    --reproducible \
    --validation
