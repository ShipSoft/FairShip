# save python objects as pickle object in ROOT file
from rootpyPickler import Pickler
from ShipGeoConfig import AttrDict
from ShipGeoConfig import ConfigRegistry
import ROOT,os,subprocess
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
def execute(f,ox,name='ShipGeo'):
    if type(ox) == type(''): ox = ConfigRegistry.register_config("basic")
    o = retrieveGitTags(ox)
    if type(f)==type("s"): fg = ROOT.TFile.Open(f,'update')
    else:                  fg = f 
    pkl = Pickler(fg)
    pkl.dump(o,name)    
    if type(f)==type("s"): fg.Close()

  
