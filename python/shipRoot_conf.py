import ROOT, atexit, sys
#-----prepare python exit-----------------------------------------------

ROOT.gInterpreter.ProcessLine('typedef double Double32_t')
def pyExit():
 x = sys.modules['__main__']
 if hasattr(x,'run'): del x.run
 if hasattr(x,'fMan'): del x.fMan
 if hasattr(x,'fRun'): del x.fRun
 pass


def configure():
 #ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
 #ROOT.basiclibs()
 ROOT.gSystem.Load("libPythia6")
 ROOT.gSystem.Load("libpythia8")
 pdg = ROOT.TDatabasePDG.Instance()
 # pythia stuff not known to ROOT
 pdg.AddParticle('system','system', 0., False, 0., 0., 'XXX', 90)
 pdg.AddParticle('p_diffr+','p_diffr+', 0., False, 0., 0., 'XXX', 9902210)
 pdg.AddParticle('f0(980)','f0(980)', 0., False, 0.07, 0., 'f0(980)', 9010221)
 atexit.register(pyExit)
