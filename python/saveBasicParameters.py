# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import contextlib
import os
import re
import subprocess

import ROOT
from ShipGeoConfig import Config


def versionFromHeader(library, header, version_macro, git_macro):
    """Version of the library that is loaded, from the version header installed with it.

    The header is next to the library's lib/ directory: in include/ of an install
    prefix (conda, cmake --install), or at the top of a build directory.
    """
    path = ROOT.gSystem.FindDynamicLibrary(ROOT.TString(library), True)
    if not path:
        return None
    prefix = os.path.dirname(os.path.dirname(path))
    for candidate in (os.path.join(prefix, "include", header), os.path.join(prefix, header)):
        with contextlib.suppress(OSError):
            with open(candidate) as f:
                macros = dict(re.findall(r'#define\s+(\w+)\s+"([^"]*)"', f.read()))
            version = macros.get(version_macro)
            if not version:
                continue
            git = macros.get(git_macro)
            return f"{version} ({git})" if git else version
    return None


def retrieveGitTags(o):
    """Record the versions this run uses, dropping any it cannot determine.

    FairShip is the Python source (FAIRSHIP_HASH from aliBuild, else its git
    commit), FairShipLibrary the compiled libraries, which differ from it when
    they come from the conda package.
    """
    versions = {"FairShip": None}
    if "FAIRSHIP_HASH" in os.environ:
        versions["FairShip"] = os.environ["FAIRSHIP_HASH"]
    else:
        source_dir = os.environ.get("FAIRSHIP", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with contextlib.suppress(subprocess.CalledProcessError, FileNotFoundError):
            versions["FairShip"] = subprocess.check_output(
                ["git", "-C", source_dir, "rev-parse", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
    versions["FairShipLibrary"] = versionFromHeader(
        "libShipData", "FairShipVersion.h", "FAIRSHIP_VERSION", "FAIRSHIP_GIT_VERSION"
    )
    versions["FairRoot"] = os.environ.get("FAIRROOT_HASH") or versionFromHeader(
        "libBase", "FairVersion.h", "FAIRROOT_VERSION", "FAIRROOT_GIT_VERSION"
    )
    for key, version in versions.items():
        if version:
            o[key] = version
        else:
            o.pop(key, None)
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
