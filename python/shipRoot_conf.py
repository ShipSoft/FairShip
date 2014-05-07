import ROOT,atexit,sys
#-----prepare python exit-----------------------------------------------
def pyExit():
 x = sys.modules['__main__']
 del x.run
 pass
def configure():
 ROOT.gROOT.LoadMacro("$VMCWORKDIR/gconfig/basiclibs.C")
 ROOT.basiclibs()
 atexit.register(pyExit)


