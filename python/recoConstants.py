# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Track-reconstruction cuts shared by the GenFit and ACTS paths.

Deliberately free of ROOT and ACTS imports so both ``shipDigiReco`` (ROOT) and
``strawReco`` (ACTS) can pull the same values in without dragging the other
fitter's dependencies along.
"""

# Minimum straw layers for a fittable track candidate; the threshold is tuned to
# the 1-plane-per-view geometry (#552). shipDigiReco applies it when building
# candidates from pattern recognition, strawReco when handing them to ACTS.
MIN_HITS_PER_TRACK = 13
