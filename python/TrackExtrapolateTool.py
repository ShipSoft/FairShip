# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from typing import Any

import ROOT
import shipunit as u

# In C++ because extrapolating with GENFIT objects created from Python made ShipAna crash at exit.
ROOT.gInterpreter.Declare("""
bool shipExtrapolateToZ(int pdg, const TVector3& pos0, const TVector3& mom0, double z, TVector3& pos, TVector3& mom) {
  genfit::RKTrackRep rep(pdg);
  genfit::StateOnPlane state(&rep);
  rep.setPosMom(state, pos0, mom0);
  try {
    rep.extrapolateToPlane(state, genfit::SharedPlanePtr(new genfit::DetPlane(TVector3(0, 0, z), TVector3(0, 0, 1))));
  } catch (genfit::Exception&) {
    return false;
  }
  pos = state.getPos();
  mom = state.getMom();
  return true;
}
""")
minNdf = 20
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
            pos, mom = ROOT.TVector3(), ROOT.TVector3()
            # muon hypothesis with the fitted charge (mu- is +13); the fitted PDG code keeps the seed's sign
            pdg = 13 if fstate.getCharge() < 0 else -13
            if not ROOT.shipExtrapolateToZ(pdg, fstate.getPos(), fstate.getMom(), zs, pos, mom):
                # Honour the contract: no valid extrapolation -> pos/mom are None.
                return False, None, None
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
