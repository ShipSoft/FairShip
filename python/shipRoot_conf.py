from __future__ import print_function
import ROOT
import atexit
import sys
import os
from pythia8_conf_utils import addHNLtoROOT
from pythia8darkphoton_conf import addDPtoROOT

# Try to check if config has been executed...
if os.environ.get('FAIRSHIP_ROOT', '') == '' and os.environ.get('Linux_Flavour_', '') == '':
   print("Do first: source config.[c]sh")
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
    ROOT.gSystem.Load("libG4clhep")
ROOT.gInterpreter.ProcessLine('typedef double Double32_t')

# -----prepare python exit-----------------------------------------------


def pyExit():
    for module in sys.modules:
        if "ROOT.genfit" in module:
            x = sys.modules['__main__']
            if hasattr(x, 'run'):
                del x.run
                print(
                    "make suicid, until better solution found to ROOT/genfit interference")
                for f in ROOT.gROOT.GetListOfFiles():
                    if f.IsWritable() and f.IsOpen(): f.Close()
                os.system('kill '+str(os.getpid()))
            if hasattr(x,'fMan'): del x.fMan
            if hasattr(x,'fRun'): del x.fRun
            return
    print("Genfit is not used. Exit normally")

def configure(darkphoton=None):
   ROOT.gROOT.ProcessLine('#include "'+os.environ["FAIRSHIP"]+'/shipdata/ShipGlobals.h"')
   pdg = ROOT.TDatabasePDG.Instance()
   # pythia stuff not known to ROOT
   pdg.AddParticle('system','system',     0., False, 0., 0., 'XXX', 90)
   pdg.AddParticle('Pomeron','Pomeron',   0., False, 0., 0., 'Pomeron', 990)
   pdg.AddParticle('p_diffr+','p_diffr+', 0., False, 0., 0., 'XXX', 9902210)
   pdg.AddParticle('n_diffr0','n_diffr0', 0., False, 0., 0., 'XXX', 9902110)
   pdg.AddParticle('J/psi[3PJ(8)]'    ,'J/psi[3PJ(8)]'    ,3.29692,False,0.,      0.,'Meson', 9942003)
   pdg.AddParticle('J/psi[1S0(8)]'    ,'J/psi[1S0(8)]'    ,3.29692,False,0.,      0.,'Meson', 9941003)
   pdg.AddParticle('f0(980)'          ,'f0(980)'          ,1.0,    False,0.0,     0.,'Meson', 9010221)
   pdg.AddParticle('psi(3770)'        ,'psi(3770)'        ,3.77315,False,0.02720, 0, 'Meson', 30443)
   pdg.AddParticle('psi(3770)[3PJ(8)]','psi(3770)[3PJ(8)]',3.97315,False,0.0,     0, 'Meson', 9942033)
   pdg.AddParticle('J/psi[3S1(8)]'    ,'J/psi[3S1(8)]'    ,3.29692,False,0.0,     0, 'Meson', 9940003)
   pdg.AddParticle('chi_0c[3S1(8)]'    ,'chi_0c[3S1(8)]'  ,3.61475,False,0.0,     0, 'Meson', 9940011)
   pdg.AddParticle('psi(2S)[1S0(8)]'   ,'psi(2S)[1S0(8)]' ,3.88611,False,0.0,     0, 'Meson', 9941103)
   pdg.AddParticle('psi(2S)[3S1(8)]'   ,'psi(2S)[3S1(8)]' ,3.88611,False,0.0,     0, 'Meson', 9940103)
   pdg.AddParticle('psi(2S)[3PJ(8)]'   ,'psi(2S)[3PJ(8)]' ,3.88611,False,0.0,     0, 'Meson', 9942103)
   pdg.AddParticle('chi_1c[3S1(8)]'    ,'chi_1c[3S1(8)]'  ,3.71066,False,0.0,     0, 'Meson', 9940023)
   pdg.AddParticle('chi_2c[3S1(8)]'    ,'chi_2c[3S1(8)]'  ,3.75620,False,0.0,     0, 'Meson', 9940005)
   pdg.AddParticle('Upsilon[3S1(8)]'   ,'Upsilon[3S1(8)]' ,9.66030,False,0.0,     0, 'Meson', 9950003)
   atexit.register(pyExit)
   if darkphoton==0: return # will be added by pythia8_conf
   if (darkphoton):
      addDPtoROOT()
   else:
      addHNLtoROOT()

