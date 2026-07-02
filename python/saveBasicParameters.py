# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import contextlib
import os
import subprocess

import ROOT
from ShipGeoConfig import Config


def retrieveGitTags(o):
    if "FAIRSHIP_HASH" in os.environ:
        o.FairShip = os.environ["FAIRSHIP_HASH"]
        if "FAIRROOT_HASH" in os.environ:
            o.FairRoot = os.environ["FAIRROOT_HASH"]
    else:
        source_dir = os.environ.get("FAIRSHIP", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with contextlib.suppress(subprocess.CalledProcessError, FileNotFoundError):
            o.FairShip = subprocess.check_output(
                ["git", "-C", source_dir, "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
    return o


def execute(f, ox, name="ShipGeo"):
    """Save geometry configuration to ROOT file as JSON string"""
    if isinstance(ox, str):
        # A string input is the JSON serialisation of the config; parse it into a
        # Config so the content is preserved and dumps_json() is available.
        ox = Config().loads_json(ox)
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
