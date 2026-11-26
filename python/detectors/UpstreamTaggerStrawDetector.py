# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import global_variables
import ROOT
from BaseDetector import BaseDetector


class UpstreamTaggerStrawDetector(BaseDetector):
    def __init__(self, name, intree, outtree=None) -> None:
        super().__init__(name, intree, outtree=outtree)

    def digitize(self) -> None:
        ship_geo = global_variables.ShipGeo
        pos_res = ship_geo.UpstreamTaggerStraw.PositionResolution
        time_res = ship_geo.UpstreamTaggerStraw.TimeResolution

        for aMCPoint in self.intree.UpstreamTaggerStrawPoint:
            aHit = ROOT.UpstreamTaggerStrawHit(aMCPoint, self.intree.t0, pos_res, time_res)
            self.det.push_back(aHit)
