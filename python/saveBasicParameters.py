# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

from ShipGeoConfig import AttrDict
from ShipGeoConfig import ConfigRegistry
import ROOT
import os
import subprocess
def retrieveGitTags(o):
    # record some basic information about version of software:
    if "FAIRSHIP_HASH" in os.environ:
        o.FairShip = os.environ['FAIRSHIP_HASH']
        o.FairSoft = '0000000000000000000000000000000000000000'
        o.FairRoot = os.environ['FAIRROOT_HASH']
    else:
      tmp = os.environ['FAIRSHIP']+'/.git/refs/remotes/origin/master'
      if os.path.isfile(tmp):
        x = subprocess.check_output(['more',tmp]).replace('\n','')
        o.FairShip = AttrDict(origin=x)
        tmp = os.environ['FAIRSHIP']+'/.git/refs/heads/master'
      if os.path.isfile(tmp):
        x = subprocess.check_output(['more',tmp]).replace('\n','')
        o.FairShip = AttrDict(local=x)
        tmp = os.environ['SIMPATH']+'/../FairSoft/.git/refs/heads/master'
      if os.path.isfile(tmp):
        x = subprocess.check_output(['more',tmp]).replace('\n','')
        o.FairSoft = AttrDict(master=x)
        tmp = os.environ['SIMPATH']+'/../FairSoft/.git/refs/heads/dev'
      if os.path.isfile(tmp):
        x = subprocess.check_output(['more',tmp]).replace('\n','')
        o.FairSoft = AttrDict(dev=x)
        tmp = os.environ['FAIRROOTPATH']+'/../FairRoot/.git/refs/heads/dev'
      if os.path.isfile(tmp):
        x = subprocess.check_output(['more',tmp]).replace('\n','')
        o.FairRoot = AttrDict(dev=x)
        tmp = os.environ['FAIRROOTPATH']+'/../FairRoot/.git/refs/heads/master'
      if os.path.isfile(tmp):
        x = subprocess.check_output(['more',tmp]).replace('\n','')
        o.FairRoot = AttrDict(master=x)
    return o
def execute(f, ox, name='ShipGeo'):
    """Save geometry configuration to ROOT file as JSON string"""
    if type(ox) == str:
        ox = ConfigRegistry.register_config("basic")
    o = retrieveGitTags(ox)

    if type(f) == str:
        fg = ROOT.TFile.Open(f, 'update')
    else:
        fg = f

    # Serialize to JSON
    json_str = o.dumps_json()

    # Save as std::string in ROOT file
    fg.cd()
    config_str = ROOT.std.string(json_str)
    fg.WriteObject(config_str, name)
    fg.Flush()

    if type(f) == str:
        fg.Close()
