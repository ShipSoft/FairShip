#!/usr/bin/env python
"""Toolkit for Analysis."""

import numpy as np
import ROOT
import shipunit as u
import yaml
from rootpyPickler import Unpickler
from ShipGeoConfig import AttrDict
from tabulate import tabulate


class selection_check:
    """Class to perform various selection checks on the candidate."""

    def __init__(self, geo_file):
        """Initialize the selection_check class with geometry and configuration."""
        self.geometry_manager = geo_file.FAIRGeom
        unpickler = Unpickler(geo_file)
        self.ship_geo = unpickler.load("ShipGeo")

        fairship = ROOT.gSystem.Getenv("FAIRSHIP")

        if self.ship_geo.DecayVolumeMedium == "helium":
            with open(fairship + "/geometry/veto_config_helium.yaml", "r") as file:
                config = yaml.safe_load(file)
                self.veto_geo = AttrDict(config)
                self.veto_geo.z0
        if self.ship_geo.DecayVolumeMedium == "vacuums":
            with open(fairship + "/geometry/veto_config_vacuums.yaml", "r") as file:
                config = yaml.safe_load(file)
                self.veto_geo = AttrDict(config)

    def access_event(self, tree):
        """Access event data."""
        self.tree = tree

    def define_candidate_time(self, candidate):
        """Calculate time associated with the candidate decay vertex using strawtubes MCPoint info."""
        t0 = self.tree.ShipEventHeader.GetEventTime()
        candidate_pos = ROOT.TVector3()
        candidate.GetVertex(candidate_pos)

        d1, d2 = candidate.GetDaughter(0), candidate.GetDaughter(1)
        d1_mc, d2_mc = self.tree.fitTrack2MC[d1], self.tree.fitTrack2MC[d2]

        time_vtx_from_strawhits = []

        for hit in self.tree.strawtubesPoint:
            if not (
                int(str(hit.GetDetectorID())[:1]) == 1
                or int(str(hit.GetDetectorID())[:1]) == 2
            ):
                continue

            if not (hit.GetTrackID() == d1_mc or hit.GetTrackID() == d2_mc):
                continue

            t_straw = hit.GetTime()

            dist = np.sqrt(
                (candidate_pos.X() - hit.GetX()) ** 2
                + (candidate_pos.Y() - hit.GetY()) ** 2
                + (candidate_pos.Z() - hit.GetZ()) ** 2
            )  # distance to the vertex in cm

            d_mom = self.tree.MCTrack[hit.GetTrackID()].GetP() / u.GeV
            mass = self.tree.MCTrack[hit.GetTrackID()].GetMass()
            v = u.c_light * d_mom / np.sqrt(d_mom**2 + (mass) ** 2)

            t_vertex = t_straw - (dist / v)

            time_vtx_from_strawhits.append(t_vertex)

        t_vtx = np.average(time_vtx_from_strawhits) + t0

        return t_vtx  # units in ns

    def impact_parameter(self, candidate):
        """Calculate the impact parameter of the candidate relative to (0,0,target.z0)."""
        candidate_pos = ROOT.TVector3()
        candidate.GetVertex(candidate_pos)

        candidate_mom = ROOT.TLorentzVector()
        candidate.Momentum(candidate_mom)
        target_point = ROOT.TVector3(0, 0, self.ship_geo.target.z0)

        projection_factor = 0
        if hasattr(candidate_mom, "P"):
            P = candidate_mom.P()
        else:
            P = candidate_mom.Mag()
        for i in range(3):
            projection_factor += (
                candidate_mom(i) / P * (target_point(i) - candidate_pos(i))
            )

        dist = 0
        for i in range(3):
            dist += (
                target_point(i)
                - candidate_pos(i)
                - projection_factor * candidate_mom(i) / P
            ) ** 2
        dist = ROOT.TMath.Sqrt(dist)

        return dist  # in cm

    def dist_to_innerwall(self, candidate):
        """Calculate the minimum distance(in XY plane) of the candidate decay vertex to the inner wall of the decay vessel. If outside the decay volume, or if distance > 100cm,Return 0."""
        candidate_pos = ROOT.TVector3()
        candidate.GetVertex(candidate_pos)
        position = (candidate_pos.X(), candidate_pos.Y(), candidate_pos.Z())

        nsteps = 8
        dalpha = 2 * ROOT.TMath.Pi() / nsteps
        min_distance = float("inf")

        node = self.geometry_manager.FindNode(*position)
        if not node:
            return 0  # is outside the decay volume

        # Loop over directions in the XY plane
        for n in range(nsteps):
            alpha = n * dalpha
            direction = (
                ROOT.TMath.Sin(alpha),
                ROOT.TMath.Cos(alpha),
                0.0,
            )  # Direction vector in XY plane
            self.geometry_manager.InitTrack(*position, *direction)
            if not self.geometry_manager.FindNextBoundary():
                continue
            # Get the distance to the boundary and update the minimum distance
            distance = self.geometry_manager.GetStep()
            min_distance = min(min_distance, distance)

        return min_distance if min_distance < 100 * u.m else 0

    def dist_to_vesselentrance(self, candidate):
        """Calculate the distance of the candidate decay vertex to the entrance of the decay vessel."""
        candidate_pos = ROOT.TVector3()
        candidate.GetVertex(candidate_pos)
        return candidate_pos.Z() - self.veto_geo.z0

    def nDOF(self, candidate):
        """Return the number of degrees of freedom (nDOF) for the particle's daughter tracks."""
        nmeas = []
        t1, t2 = candidate.GetDaughter(0), candidate.GetDaughter(1)

        for tr in [t1, t2]:
            fit_status = self.tree.FitTracks[tr].getFitStatus()
            nmeas.append(
                int(round(fit_status.getNdf()))
            )  # nmeas.append(fit_status.getNdf())

        return np.array(nmeas)

    def daughtermomentum(self, candidate):
        """Return the momentum(Mag) of the particle's daughter tracks."""
        daughter_mom = []
        t1, t2 = candidate.GetDaughter(0), candidate.GetDaughter(1)
        for trD in [t1, t2]:
            x = self.tree.FitTracks[trD]
            xx = x.getFittedState()
            daughter_mom.append((xx.getMom().Mag()))

        return np.array(daughter_mom)

    def invariant_mass(self, candidate):
        """Invariant mass of the candidate."""
        return candidate.GetMass()

    def DOCA(self, candidate):
        """Distance of Closest Approach."""
        return candidate.GetDoca()

    def is_in_fiducial(self, candidate):
        """Check if the candidate decay vertex is within the Fiducial Volume."""
        candidate_pos = ROOT.TVector3()
        candidate.GetVertex(candidate_pos)

        if candidate_pos.Z() > self.ship_geo.TrackStation1.z:
            return False
        if candidate_pos.Z() < self.veto_geo.z0:
            return False

        # if self.dist2InnerWall(candidate)<=5*u.cm: return False

        vertex_node = ROOT.gGeoManager.FindNode(
            candidate_pos.X(), candidate_pos.Y(), candidate_pos.Z()
        )
        vertex_elem = vertex_node.GetVolume().GetName()
        if not vertex_elem.startswith("DecayVacuum_"):
            return False
        return True

    def chi2nDOF(self, candidate):
        """Return the reduced chi^2 of the particle's daughter tracks."""
        t1, t2 = candidate.GetDaughter(0), candidate.GetDaughter(1)

        chi2ndf = []
        for tr in [t1, t2]:
            fit_status = self.tree.FitTracks[tr].getFitStatus()
            chi2ndf.append(fit_status.getChi2() / fit_status.getNdf())

        return np.array(chi2ndf)

    def preselection_cut(self, candidate, IP_cut=250, show_table=False):
        """
        Umbrella method to apply the pre-selection cuts on the candidate.

        show_table=True tabulates the pre-selection parameters.
        """
        flag = True

        if len(self.tree.Particles) != 1:
            flag = False
        if not (self.is_in_fiducial(candidate)):
            flag = False
        if self.dist_to_innerwall(candidate) <= 5 * u.cm:
            flag = False
        if self.dist_to_vesselentrance(candidate) <= 100 * u.cm:
            flag = False
        if self.impact_parameter(candidate) >= IP_cut * u.cm:
            flag = False
        if self.DOCA(candidate) >= 1 * u.cm:
            flag = False
        if np.any(self.nDOF(candidate) <= 25):
            flag = False
        if np.any(self.chi2nDOF(candidate) >= 5):
            flag = False
        if np.any(self.daughtermomentum(candidate) <= 1 * u.GeV):
            flag = False

        if show_table:
            table = [
                [
                    "Number of candidates in event",
                    len(self.tree.Particles),
                    "==1",
                    len(self.tree.Particles) == 1,
                ],
                [
                    "Time @ decay vertex (ns)",
                    self.define_candidate_time(candidate),
                    "",
                    "",
                ],
                [
                    "Impact Parameter (cm)",
                    self.impact_parameter(candidate),
                    f"IP < {IP_cut*u.cm} cm",
                    self.impact_parameter(candidate) < IP_cut * u.cm,
                ],
                [
                    "DOCA (cm)",
                    self.DOCA(candidate),
                    "DOCA < 1 cm",
                    self.DOCA(candidate) < 1 * u.cm,
                ],
                [
                    "Is within Fiducial Volume?",
                    self.is_in_fiducial(candidate),
                    "True",
                    self.is_in_fiducial(candidate),
                ],
                [
                    "Dist2InnerWall (cm)",
                    self.dist_to_innerwall(candidate),
                    "> 5 cm",
                    self.dist_to_innerwall(candidate) > 5 * u.cm,
                ],
                [
                    "Dist2VesselEntrance (cm)",
                    self.dist_to_vesselentrance(candidate),
                    "> 100 cm",
                    self.dist_to_vesselentrance(candidate) > 100 * u.cm,
                ],
                ["Invariant Mass (GeV)", self.invariant_mass(candidate), "", ""],
                [
                    "Daughter Momentum [d1, d2] (GeV)",
                    self.daughtermomentum(candidate),
                    "> 1 GeV",
                    np.all(self.daughtermomentum(candidate) > 1 * u.GeV),
                ],
                [
                    "Degrees of Freedom [d1, d2]",
                    self.nDOF(candidate),
                    "> 25",
                    np.all(self.nDOF(candidate) > 25),
                ],
                [
                    "Reduced Chi^2 [d1, d2]",
                    self.chi2nDOF(candidate),
                    "< 5",
                    np.all(self.chi2nDOF(candidate) < 5),
                ],
                ["\033[1mPre-selection passed:\033[0m", "", "", flag],
            ]

            for row in table:
                row[3] = (
                    f"\033[1;32m{row[3]}\033[0m"
                    if row[3]
                    else f"\033[1;31m{row[3]}\033[0m"
                )  # Green for True, Red for False

            print(
                tabulate(
                    table,
                    headers=[
                        "Parameter",
                        "Value",
                        "Pre-selection cut",
                        "Pre-selection Check",
                    ],
                    tablefmt="grid",
                )
            )
        return flag
