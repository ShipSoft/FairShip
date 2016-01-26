# save python objects as pickle object in ROOT file
from rootpyPickler import Pickler
from ShipGeoConfig import AttrDict
import ROOT,os,subprocess
def execute(f,o):
    # record some basic information about version of software:
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
    fg = ROOT.TFile.Open(f,'update')
    pkl=Pickler(fg)
    pkl.dump(o,'ShipGeo')
    fg.Close()
  
