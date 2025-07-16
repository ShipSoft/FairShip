import ROOT
import os
import subprocess

from fairship.utils.rootpy_pickler import Pickler
from fairship.ShipGeoConfig import AttrDict, ConfigRegistry

def save_basic_parameters(f,ox,name='ShipGeo'):
    """Save python objects as pickle object in ROOT file."""

    if type(ox) == str: ox = ConfigRegistry.register_config("basic")
    o = _retrieveGitTags(ox)
    if type(f)==str: fg = ROOT.TFile.Open(f,'update')
    else:                  fg = f
    pkl = Pickler(fg)
    pkl.dump(o,name)
    if type(f)==str: fg.Close()

def _retrieveGitTags(o):
    """Record some basic information about version of fairship software."""
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
