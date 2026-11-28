# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Print Pythia8's particle data and decay table for one PDG code.
import sys

import pythia8

id = int(sys.argv[1])
pythia = pythia8.Pythia("", False)
pythia.particleData.list(id)
