# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import ROOT
from BaseDetector import BaseDetector


class timeDetector(BaseDetector):
    def __init__(self, name, intree, outtree=None) -> None:
        super().__init__(name, intree, outtree=outtree)

    def digitize(self) -> None:
        """Digitize timing detector MC hits.

        One hit is created per TimeDetPoint, at the same index. Per bar, the hit
        from the point with the earliest true (unsmeared) time is marked valid,
        all others invalid.

        The selection uses the MC time rather than the smeared TDC values:
        points in the same bar (e.g. a muon and its delta electrons) belong to
        the same light pulse, so comparing independently smeared TDCs would pick
        a random point and often invalidate the primary's hit.
        """
        earliest_per_det_id = {}
        points = self.intree.TimeDetPoint
        for index, point in enumerate(points):
            self.det.push_back(ROOT.TimeDetHit(point, self.intree.t0))
            detector_id = point.GetDetectorID()
            earliest = earliest_per_det_id.get(detector_id)
            if earliest is None:
                earliest_per_det_id[detector_id] = index
            elif point.GetTime() < points[earliest].GetTime():
                self.det[earliest].setInvalid()
                earliest_per_det_id[detector_id] = index
            else:
                self.det[index].setInvalid()
