import ROOT, atexit, sys, os
from pythia8_conf import addHNLtoROOT
from pythia8darkphoton_conf import addDPtoROOT

# Try to check if config has been executed...
if os.environ.get('Linux_Flavour_','') == '':
   print "Do first: source config.[c]sh"
   quit()

# When on Darwin load all needed shared libs as DYLD_LIBRARY_PATH is not
# passed to system Python out of security reasons...
if sys.platform == 'darwin':
   # Load FairRoot libraries
   ROOT.gSystem.Load('libFairTools')
   ROOT.gSystem.Load('libParBase')
   ROOT.gSystem.Load('libGeoBase')
   ROOT.gSystem.Load('libMbsAPI')
   ROOT.gSystem.Load('libBase')
   # Load FairShip libraries
   ROOT.gSystem.Load('libShipPassive')
   ROOT.gSystem.Load('libShipField')
   ROOT.gSystem.Load('libcharmdet')
   ROOT.gSystem.Load('libveto')
   ROOT.gSystem.Load('libnutaudet')
   ROOT.gSystem.Load('libstrawtubes')
   ROOT.gSystem.Load('libecal')
   ROOT.gSystem.Load('libhcal')
   ROOT.gSystem.Load('libmuon')
   ROOT.gSystem.Load('libpid')
   ROOT.gSystem.Load('libpreshower')
   ROOT.gSystem.Load('libgenfit')
   ROOT.gSystem.Load("libPythia6")
   ROOT.gSystem.Load("libpythia8")
   ROOT.gSystem.Load('libShipGen')
   ROOT.gSystem.Load('libShipData')
else:
    ROOT.gSystem.Load("libPythia6")
    ROOT.gSystem.Load("libpythia8")
ROOT.gInterpreter.ProcessLine('typedef double Double32_t')

#-----prepare python exit-----------------------------------------------
def pyExit():
   x = sys.modules['__main__']
   if hasattr(x,'run'): del x.run
   if hasattr(x,'fMan'): del x.fMan
   if hasattr(x,'fRun'): del x.fRun
   pass

def configure(darkphoton=None):
   #ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
   #ROOT.basiclibs()
   pdg = ROOT.TDatabasePDG.Instance()
   # pythia stuff not known to ROOT
   pdg.AddParticle('system','system', 0., False, 0., 0., 'XXX', 90)
   pdg.AddParticle('p_diffr+','p_diffr+', 0., False, 0., 0., 'XXX', 9902210)
   pdg.AddParticle('f0(980)','f0(980)', 0., False, 0.07, 0., 'f0(980)', 9010221)
   if (darkphoton):
      addDPtoROOT()
   else:
      addHNLtoROOT()
   atexit.register(pyExit)
