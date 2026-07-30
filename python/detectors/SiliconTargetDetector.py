# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from collections import defaultdict

import ROOT
from BaseDetector import BaseDetector


class SiliconTargetDetector(BaseDetector):
    def __init__(self, name, intree, branchName=None, outtree=None) -> None:
        super().__init__(name, intree, branchName, outtree=outtree)

    def digitize(self) -> None:
        """Group SiliconTargetPoints by detector ID and build one SiliconTargetHit per ID."""
        pointsByDetID = defaultdict(list)
        for point in self.intree.SiliconTargetPoint:
            pointsByDetID[point.GetDetectorID()].append(point)

        for detID, pts in pointsByDetID.items():
            allPoints = ROOT.std.vector("SiliconTargetPoint*")()
            for p in pts:
                allPoints.push_back(p)
            det_hit = ROOT.SiliconTargetHit(detID, allPoints)
            self.det.push_back(det_hit)
