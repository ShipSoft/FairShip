# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from typing import Any

import ROOT
import shipunit as u

minNdf = 20
parallelToZ = ROOT.TVector3(0.0, 0.0, 1.0)
top = ROOT.gGeoManager.GetTopVolume()
# Runge-Kutta extrapolation is done up to the scoring plane (former SplitCal
# position); beyond it, tracks are extrapolated linearly.
if top.GetNode("CaloScoringPlane_1"):
    z_ecal = top.GetNode("CaloScoringPlane_1").GetMatrix().GetTranslation()[2]
else:
    print("TrackExtrapolate tool: Error, no scoring plane present")
    z_ecal = 100 * u.m


def extrapolateToPlane(fT, z) -> tuple[bool, Any, Any]:
    # extrapolate to a plane perpendicular to beam direction (z).
    # When rc is False, pos and mom are None — callers must check rc first.
    rc, pos, mom = False, None, None
    fst = fT.getFitStatus()
    if fst.isFitConverged() and fst.getNdf() > minNdf:
        # test for fit status for each point
        if fT.getPoint(0).getFitterInfo() and fT.getPoint(1).getFitterInfo():
            fstate0, fstate1 = fT.getFittedState(0), fT.getFittedState(1)
            fPos0, fPos1 = fstate0.getPos(), fstate1.getPos()
            if abs(z - fPos0.z()) < abs(z - fPos1.z()):
                fstate = fstate0
            else:
                fstate = fstate1
            zs = min(z, z_ecal)
            # muon hypothesis with the fitted charge (mu- is +13); the fitted PDG code keeps the seed's sign
            rep = ROOT.genfit.RKTrackRep(13 if fstate.getCharge() < 0 else -13)
            state = ROOT.genfit.StateOnPlane(rep)
            rep.setPosMom(state, fstate.getPos(), fstate.getMom())
            plane = ROOT.genfit.DetPlane(ROOT.TVector3(0.0, 0.0, zs), parallelToZ)
            ROOT.SetOwnership(plane, False)  # owned by the SharedPlanePtr
            try:
                rep.extrapolateToPlane(state, ROOT.genfit.SharedPlanePtr(plane))
            except Exception:
                # Honour the contract: no valid extrapolation -> pos/mom are None.
                return False, None, None
            pos, mom = state.getPos(), state.getMom()
            if z > z_ecal:
                # RK only reaches z_ecal; continue with linear extrapolation
                px, py, pz = mom.X(), mom.Y(), mom.Z()
                if pz == 0:
                    # cannot extrapolate in z with zero longitudinal momentum
                    return False, None, None
                lam = (z - pos.Z()) / pz
                pos = ROOT.TVector3(pos.X() + lam * px, pos.Y() + lam * py, z)
            rc = True
    return rc, pos, mom
