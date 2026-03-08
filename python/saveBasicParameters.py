# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

import ROOT

if TYPE_CHECKING:
    from ship_geo_config_types import ShipGeoConfig


def retrieveGitTags(o: ShipGeoConfig) -> ShipGeoConfig:
    # record some basic information about version of software:
    if "FAIRSHIP_HASH" in os.environ:
        o.FairShip = os.environ["FAIRSHIP_HASH"]
        o.FairRoot = os.environ["FAIRROOT_HASH"]
    else:
        tmp = os.environ["FAIRSHIP"] + "/.git/refs/remotes/origin/master"
        if os.path.isfile(tmp):
            x = subprocess.check_output(["more", tmp]).decode().replace("\n", "")
            o.FairShip = {"origin": x}
            tmp = os.environ["FAIRSHIP"] + "/.git/refs/heads/master"
        if os.path.isfile(tmp):
            x = subprocess.check_output(["more", tmp]).decode().replace("\n", "")
            o.FairShip = {"local": x}
            tmp = os.environ["FAIRROOTPATH"] + "/../FairRoot/.git/refs/heads/dev"
        if os.path.isfile(tmp):
            x = subprocess.check_output(["more", tmp]).decode().replace("\n", "")
            o.FairRoot = {"dev": x}
            tmp = os.environ["FAIRROOTPATH"] + "/../FairRoot/.git/refs/heads/master"
        if os.path.isfile(tmp):
            x = subprocess.check_output(["more", tmp]).decode().replace("\n", "")
            o.FairRoot = {"master": x}
    return o


def execute(f, ox: ShipGeoConfig | str, name="ShipGeo"):
    """Save geometry configuration to ROOT file as JSON string"""
    if isinstance(ox, str):
        from ship_geo_config_types import ShipGeoConfig as SGC

        ox = SGC()
    o = retrieveGitTags(ox)

    if isinstance(f, str):
        fg = ROOT.TFile.Open(f, "update")
    else:
        fg = f

    # Serialize to JSON
    json_str = o.dumps_json()

    # Save as std::string in ROOT file
    fg.cd()
    config_str = ROOT.std.string(json_str)
    fg.WriteObject(config_str, name)
    fg.Flush()

    if isinstance(f, str):
        fg.Close()
