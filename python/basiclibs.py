# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Macro for loading basic libraries used with both Geant3 and Geant4
from ROOT import gSystem, gROOT

# For ROOT >= 6.32, TPythia6 is not included in ROOT and must be loaded from EGPythia6
# For ROOT < 6.32, TPythia6 is built into libEG
root_version = gROOT.GetVersionInt()
if root_version >= 63200:
    # Load external EGPythia6 for ROOT >= 6.32
    gSystem.Load("libEGPythia6.so")
gSystem.Load("libPythia6.so")
gSystem.Load("libpythia8.so")
