# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Digitisation of the scoring plane with electron / hadron / muon identification.

The identification itself is done by the C++ class CaloScoringPlanePID
(CaloScoringPlane/CaloScoringPlanePID.h), which reads energy-dependent 3x3 confusion
matrices from a YAML file (ShipReco.py --caloScoringPlanePID) and interpolates
them at the particle energy. See CaloScoringPlane/README.md.
"""

import logging

import global_variables
import ROOT
from BaseDetector import BaseDetector

logger = logging.getLogger(__name__)


class CaloScoringPlaneDetector(BaseDetector):
    """One CaloScoringPlaneHit per accepted CaloScoringPlanePoint.

    Output branches: ``Digi_CaloScoringPlaneHits`` and ``digiCaloScoringPlane2MC``
    (per hit, the list with the MC track index).
    """

    def __init__(self, name, intree, outtree=None) -> None:
        super().__init__(name, intree, mcBranchName="digiCaloScoringPlane2MC", outtree=outtree)
        cfg = global_variables.ShipGeo.CaloScoringPlane
        self.pos_res = cfg.get("PositionResolution", 0.0)
        self.time_res = cfg.get("TimeResolution", 0.0)
        self.forward_only = cfg.get("ForwardOnly", True)
        self.ignored = {abs(int(p)) for p in cfg.get("IgnoredPdg", [12, 14, 16])}

        pid_file = getattr(global_variables, "caloScoringPlanePIDFile", None)
        if pid_file:
            self.pid = ROOT.CaloScoringPlanePID(pid_file)
        else:
            logger.warning("CaloScoringPlane PID: no --caloScoringPlanePID file given, using perfect PID")
            self.pid = ROOT.CaloScoringPlanePID()
        self.pid.Print()

    def digitize(self) -> None:
        t0 = self.intree.t0
        for point in self.intree.CaloScoringPlanePoint:
            if abs(point.PdgCode()) in self.ignored:
                continue
            if self.forward_only and point.GetPz() <= 0:
                continue
            species = self.pid.Identify(point)
            self.det.push_back(ROOT.CaloScoringPlaneHit(point, t0, self.pos_res, self.time_res, species))
            if self.MCdet is not None:  # always set (mcBranchName given); narrows the type
                links = ROOT.std.vector("int")()
                links.push_back(point.GetTrackID())
                self.MCdet.push_back(links)
