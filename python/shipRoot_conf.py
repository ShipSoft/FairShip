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
 ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
 ROOT.basiclibs()
 atexit.register(pyExit)
