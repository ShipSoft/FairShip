# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

import ROOT
from BaseDetector import BaseDetector


class muonDetector(BaseDetector):
    def __init__(self, name, intree, outtree=None):
        super().__init__(name, intree, outtree=outtree)

    def digitize(self):
        """Digitize muon detector MC hits.

        The earliest hit per detector will be marked valid, all later ones invalid.
        """
        earliest_per_det_id = {}
        for index, point in enumerate(self.intree.muonPoint):
            hit = ROOT.muonHit(point, self.intree.t0)
            self.det.push_back(hit)
            detector_id = hit.GetDetectorID()
            if hit.isValid():
                if detector_id in earliest_per_det_id:
                    earliest = earliest_per_det_id[detector_id]
                    if self.det[earliest].GetDigi() > hit.GetDigi():
                        # second hit with smaller tdc
                        self.det[earliest].setValidity(0)
                        earliest_per_det_id[detector_id] = index
                    else:
                        self.det[index].setValidity(0)
                else:
                    earliest_per_det_id[detector_id] = index
