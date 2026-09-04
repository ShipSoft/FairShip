# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Unified access to GenFit and ACTS fitted-track branches.

Reconstruction writes either GenFit tracks (branch ``FitTracks``, default)
or ACTS tracks (branch ``RecoTracks``, with ``--trackFitter acts``).
Analysis code can use these helpers to support both output formats without
caring which fitter produced the file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import ROOT


@dataclass
class TrackInfo:
    """Fitter-agnostic summary of one fitted track.

    ``mom``, ``dir``, ``pos`` and the momentum uncertainties are only
    available when ``converged`` is true; they are ``None`` otherwise.
    """

    converged: bool
    ndf: float
    chi2: float  # total chi2, not chi2/ndf
    n_points: int
    mom: ROOT.TVector3 | None = None
    dir: ROOT.TVector3 | None = None
    pos: ROOT.TVector3 | None = None
    sigma_px: float | None = None
    sigma_py: float | None = None
    sigma_pz: float | None = None


def uses_acts(tree) -> bool:
    """Return True if the tree holds ACTS tracks (RecoTracks branch)."""
    return bool(tree.GetBranch("RecoTracks"))


def get_tracks(tree):
    """Return the fitted-track branch, whichever fitter produced it."""
    return tree.RecoTracks if uses_acts(tree) else tree.FitTracks


def track_info(track, acts: bool) -> TrackInfo:
    """Summarize a fitted track from either fitter into a TrackInfo."""
    if acts:
        mom = ROOT.TVector3(track.px(), track.py(), track.pz())
        cov = track.GetCovarianceElements()
        return TrackInfo(
            converged=True,  # only successful ACTS fits are persisted
            ndf=track.nDoF(),
            chi2=track.chi2(),
            n_points=track.nMeasurements(),
            mom=mom,
            dir=mom.Unit(),
            pos=ROOT.TVector3(track.x(), track.y(), track.z()),
            sigma_px=math.sqrt(cov[15]),
            sigma_py=math.sqrt(cov[18]),
            sigma_pz=math.sqrt(cov[20]),
        )
    fit_status = track.getFitStatus()
    info = TrackInfo(
        converged=fit_status.isFitConverged(),
        ndf=fit_status.getNdf(),
        chi2=fit_status.getChi2(),
        n_points=track.getNumPoints(),
    )
    try:
        fitted_state = track.getFittedState()
    except Exception:
        return info
    cov = fitted_state.get6DCov()
    info.mom = ROOT.TVector3(fitted_state.getMom())
    info.dir = ROOT.TVector3(fitted_state.getDir())
    info.pos = ROOT.TVector3(fitted_state.getPos())
    info.sigma_px = math.sqrt(cov[3][3])
    info.sigma_py = math.sqrt(cov[4][4])
    info.sigma_pz = math.sqrt(cov[5][5])
    return info
