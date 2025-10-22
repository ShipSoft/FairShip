# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

import ROOT
from BaseDetector import BaseDetector


class timeDetector(BaseDetector):
    def __init__(self, name, intree, outtree=None):
        super().__init__(name, intree, outtree=outtree)

    def digitize(self):
        """Digitize timing detector MC hits.

        The earliest hit per straw will be marked valid, all later ones invalid.
        """
        earliest_per_det_id = {}
        for index, point in enumerate(self.intree.TimeDetPoint):
            hit = ROOT.TimeDetHit(point, self.intree.t0)
            self.det.push_back(hit)
            detector_id = hit.GetDetectorID()
            if hit.isValid():
                if detector_id in earliest_per_det_id:
                    times = hit.GetMeasurements()
                    earliest = earliest_per_det_id[detector_id]
                    reference_times = self.det[earliest].GetMeasurements()
                    # this is not really correct, only first attempt
                    # case that one measurement only is earlier not taken into account
                    # SetTDC(Float_t val1, Float_t val2)
                    if reference_times[0] > times[0] or reference_times[1] > times[1]:
                        # second hit with smaller tdc
                        self.det[earliest].setInvalid()
                        earliest_per_det_id[detector_id] = index
                    else:
                        self.det[index].setInvalid()
                else:
                    earliest_per_det_id[detector_id] = index
